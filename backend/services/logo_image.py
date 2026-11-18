"""Company logos uploaded by Admin: checked and tidied before saving, so every logo shows
sharp and at a sensible size in the app header, Admin cards, the web portal and emails.

- Must be a real image (PNG / JPG / WEBP), at most MAX_UPLOAD_BYTES.
- At least MIN_WIDTH x MIN_HEIGHT -- smaller logos look blurry when stretched.
- Empty margins (a plain border the same colour as the corners, or fully transparent) are
  trimmed, so the logo itself fills its box instead of looking small.
- Scaled down to fit MAX_WIDTH x MAX_HEIGHT (never up), keeping its shape.
- Always saved as PNG (transparency kept).

Recommended upload: a wide logo, PNG with a transparent background, about 600 x 200 px.
"""
import io

from PIL import Image, ImageChops, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_WIDTH, MIN_HEIGHT = 200, 60
MAX_WIDTH, MAX_HEIGHT = 900, 300
RECOMMENDED = "a wide logo, PNG with a transparent background, about 600 × 200 px"
_TRIM_TOLERANCE = 12  # how close to the corner colour still counts as "margin"
_PADDING_RATIO = 0.04  # keep a little breathing room after trimming


class LogoError(ValueError):
    """Something Admin must fix: wrong file, too small, too large."""


def _trim(img: Image.Image) -> Image.Image:
    """Crops away a plain border: fully transparent pixels, or pixels matching the top-left
    corner's colour (e.g. a white background around a JPG logo)."""
    rgba = img.convert("RGBA")
    alpha_box = rgba.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if alpha_box is None:
        raise LogoError("The logo is empty (fully transparent)")
    if alpha_box != (0, 0, rgba.width, rgba.height):
        box = alpha_box
    else:
        corner = rgba.getpixel((0, 0))
        background = Image.new("RGBA", rgba.size, corner)
        diff = ImageChops.difference(rgba, background).convert("L")
        box = diff.point(lambda v: 255 if v > _TRIM_TOLERANCE else 0).getbbox()
        if box is None:
            raise LogoError("The logo is a single plain colour")
    left, top, right, bottom = box
    pad = int(max(right - left, bottom - top) * _PADDING_RATIO)
    box = (max(0, left - pad), max(0, top - pad), min(rgba.width, right + pad), min(rgba.height, bottom + pad))
    return rgba.crop(box)


def normalize_logo(raw: bytes) -> tuple[bytes, tuple[int, int]]:
    """Returns (PNG bytes, (width, height)) ready to store, or raises LogoError."""
    if not raw:
        raise LogoError("The file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise LogoError(f"The logo file is too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB). Use {RECOMMENDED}.")
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise LogoError("This file isn't an image. Upload a PNG or JPG logo.") from exc
    if img.width < MIN_WIDTH or img.height < MIN_HEIGHT:
        raise LogoError(
            f"The logo is too small ({img.width} × {img.height} px). "
            f"Use at least {MIN_WIDTH} × {MIN_HEIGHT} px; best is {RECOMMENDED}."
        )
    img = _trim(img)
    img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)  # only ever shrinks
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue(), img.size
