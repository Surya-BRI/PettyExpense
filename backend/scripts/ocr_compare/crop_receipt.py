"""Standalone receipt-boundary crop, for comparison against the no-crop baseline.
Not wired into services/ocr_service.py -- this is a comparison tool only, per the
baseline-first plan. Standard document-scanner approach: detect edges on a small
working copy, find the largest quadrilateral contour, perspective-warp the FULL
resolution original to that boundary. Falls back to the original image untouched
if no confident quadrilateral is found -- never guesses a crop that might cut
off real receipt content.
Usage as a library: crop_to_receipt(image_bytes) -> (cropped_bytes, info_dict)
Usage standalone: python crop_receipt.py <image_path> <output_path>
"""
import sys
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

_WORKING_MAX_SIDE = 1000
_MIN_AREA_FRACTION = 0.20
_PAD_FRACTION = 0.01


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _find_receipt_quad(working_img: np.ndarray) -> "np.ndarray | None":
    gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    working_area = working_img.shape[0] * working_img.shape[1]

    for c in contours:
        area = cv2.contourArea(c)
        if area < working_area * _MIN_AREA_FRACTION:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype("float32")
    return None


def crop_to_receipt(image_bytes: bytes) -> tuple[bytes, dict]:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    full = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if full is None:
        return image_bytes, {"cropped": False, "reason": "decode_failed"}

    h, w = full.shape[:2]
    scale = _WORKING_MAX_SIDE / max(h, w) if max(h, w) > _WORKING_MAX_SIDE else 1.0
    working = cv2.resize(full, (int(w * scale), int(h * scale))) if scale < 1.0 else full.copy()

    quad = _find_receipt_quad(working)
    if quad is None:
        return image_bytes, {"cropped": False, "reason": "no_confident_quad_found", "input_dims": [w, h]}

    quad_full = quad / scale
    rect = _order_points(quad_full)
    (tl, tr, br, bl) = rect

    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = int(max(width_a, width_b))
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = int(max(height_a, height_b))

    if max_width < 10 or max_height < 10:
        return image_bytes, {"cropped": False, "reason": "degenerate_quad", "input_dims": [w, h]}

    pad_x = int(max_width * _PAD_FRACTION)
    pad_y = int(max_height * _PAD_FRACTION)
    dst = np.array(
        [
            [pad_x, pad_y],
            [max_width - 1 + pad_x, pad_y],
            [max_width - 1 + pad_x, max_height - 1 + pad_y],
            [pad_x, max_height - 1 + pad_y],
        ],
        dtype="float32",
    )
    out_w, out_h = max_width + 2 * pad_x, max_height + 2 * pad_y
    matrix = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(full, matrix, (out_w, out_h))

    is_success, buf = cv2.imencode(".jpg", warped, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not is_success:
        return image_bytes, {"cropped": False, "reason": "encode_failed", "input_dims": [w, h]}

    quad_area_fraction = cv2.contourArea(quad) / (working.shape[0] * working.shape[1])
    return buf.tobytes(), {
        "cropped": True,
        "input_dims": [w, h],
        "cropped_dims": [out_w, out_h],
        "quad_area_fraction_of_working_image": round(float(quad_area_fraction), 3),
    }


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        data = f.read()
    cropped_bytes, info = crop_to_receipt(data)
    with open(dst, "wb") as f:
        f.write(cropped_bytes)
    print(info)


if __name__ == "__main__":
    main()
