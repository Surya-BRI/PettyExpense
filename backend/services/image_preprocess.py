"""
Image quality assessment + preprocessing for OCR.

assess_quality() checks sharpness, brightness, contrast, and resolution;
preprocess_if_needed() applies CLAHE → sharpen → denoise → deskew → 2x upscale
only when the image actually needs it, leaving clean prints untouched.
"""
import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# --- Quality thresholds -------------------------------------------------------
# Each metric has a threshold below which the image is considered poor quality.
# Calibrated so clean printed receipts pass and WhatsApp-compressed/dark photos fail.

_SHARPNESS_MIN  = 80.0   # Laplacian variance — below this the image is blurry
_BRIGHTNESS_MIN = 95.0   # Mean L channel (LAB, 0-255) — below this the image is dark
_CONTRAST_MIN   = 35.0   # Std-dev of L channel — below this the image is flat/low-contrast
_MIN_SIDE_PX    = 400    # Shorter pixel dimension — below this needs upscaling (raised from 600 to skip clean screenshots at 400-600px)


@dataclass
class ImageQuality:
    sharpness: float
    brightness: float
    contrast: float
    min_side: int
    needs_sharpen: bool
    needs_clahe: bool
    needs_upscale: bool
    needs_deskew: bool

    @property
    def needs_preprocessing(self) -> bool:
        return self.needs_sharpen or self.needs_clahe or self.needs_upscale or self.needs_deskew

    def summary(self) -> str:
        flags = []
        if self.needs_clahe:    flags.append(f"clahe(brightness={self.brightness:.0f},contrast={self.contrast:.0f})")
        if self.needs_sharpen:  flags.append(f"sharpen(lap={self.sharpness:.0f})")
        if self.needs_upscale:  flags.append(f"upscale({self.min_side}px)")
        if self.needs_deskew:   flags.append("deskew")
        return ",".join(flags) if flags else "clean"


def assess_quality(image_bytes: bytes) -> ImageQuality:
    """Decode the image and measure sharpness, brightness, contrast, resolution."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        # Can't decode — treat as needing everything
        return ImageQuality(0, 0, 0, 0, True, True, True, True)

    h, w = img.shape[:2]
    min_side = min(h, w)

    # Sharpness: Laplacian variance on grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Brightness + contrast: L channel of LAB
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0].astype(np.float32)
    brightness = float(l_channel.mean())
    contrast   = float(l_channel.std())

    # Deskew: run a quick skew estimate; only flag if measurably tilted
    try:
        from deskew import determine_skew
        angle = determine_skew(gray)
        # Skip deskew on dark/dim images — determine_skew misfires on low-brightness
        # photos because it picks up background shadows rather than text lines.
        _DESKEW_MIN_BRIGHTNESS = 120.0
        _angle_ok = angle is not None and 1.5 < abs(angle) < 15.0
        needs_deskew = _angle_ok and brightness >= _DESKEW_MIN_BRIGHTNESS
    except Exception:
        needs_deskew = False

    return ImageQuality(
        sharpness  = sharpness,
        brightness = brightness,
        contrast   = contrast,
        min_side   = min_side,
        needs_sharpen = sharpness  < _SHARPNESS_MIN,
        needs_clahe   = brightness < _BRIGHTNESS_MIN or contrast < _CONTRAST_MIN,
        needs_upscale = min_side   < _MIN_SIDE_PX,
        needs_deskew  = needs_deskew,
    )


def preprocess_image(image_bytes: bytes, quality: ImageQuality | None = None) -> bytes:
    """
    Apply only the steps the image actually needs.
    Pass a pre-computed ImageQuality to avoid decoding twice.
    """
    if quality is None:
        quality = assess_quality(image_bytes)
    if not quality.needs_preprocessing:
        return image_bytes

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return image_bytes

    # 1. Upscale first so all subsequent ops work on more pixels
    if quality.needs_upscale:
        img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2), interpolation=cv2.INTER_CUBIC)

    # 2. CLAHE on the L channel (LAB) for adaptive contrast + brightness
    if quality.needs_clahe:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    # 3. Sharpen
    if quality.needs_sharpen:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        img = cv2.filter2D(img, -1, kernel)
        # Light denoise after sharpening to suppress amplified noise
        img = cv2.fastNlMeansDenoisingColored(img, None, h=5, hColor=5,
                                               templateWindowSize=7, searchWindowSize=21)

    # 4. Deskew
    if quality.needs_deskew:
        try:
            from deskew import determine_skew
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            angle = determine_skew(gray)
            if angle is not None and abs(angle) > 0.3:
                (h, w) = img.shape[:2]
                M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                img = cv2.warpAffine(img, M, (w, h),
                                     flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            pass

    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buf.tobytes() if ok else image_bytes


def preprocess_if_needed(image_bytes: bytes) -> tuple[bytes, ImageQuality]:
    """Assess quality, preprocess only if needed; return (final_bytes, quality_info)."""
    quality = assess_quality(image_bytes)
    logger.debug("Image quality: %s", quality.summary())
    result = preprocess_image(image_bytes, quality)
    return result, quality
