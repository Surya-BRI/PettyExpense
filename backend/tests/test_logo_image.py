import io

import pytest
from PIL import Image, ImageDraw

from services.logo_image import MAX_HEIGHT, MAX_WIDTH, LogoError, normalize_logo


def _image(size, background, fmt="PNG", mark_box=None, mark=(10, 60, 140, 255)):
    img = Image.new("RGBA" if fmt == "PNG" else "RGB", size, background)
    if mark_box:
        ImageDraw.Draw(img).rectangle(mark_box, fill=mark if fmt == "PNG" else mark[:3])
    out = io.BytesIO()
    img.save(out, format=fmt)
    return out.getvalue()


def _open(png: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(png))
    assert img.format == "PNG"
    return img


def test_white_margins_around_a_jpg_logo_are_trimmed_and_it_becomes_png():
    # 1000 x 600 white JPG with the logo in a 400 x 120 area in the middle.
    raw = _image((1000, 600), "white", fmt="JPEG", mark_box=(300, 240, 699, 359))
    png, (w, h) = normalize_logo(raw)
    img = _open(png)
    assert (w, h) == img.size
    # Trimmed to the logo plus a little padding -- not the whole white page.
    assert 400 <= w <= 440 and 120 <= h <= 160


def test_transparent_margins_are_trimmed_and_transparency_kept():
    raw = _image((800, 400), (0, 0, 0, 0), mark_box=(100, 100, 699, 299))
    png, (w, h) = normalize_logo(raw)
    img = _open(png)
    assert img.mode == "RGBA"
    assert 600 <= w <= 650 and 200 <= h <= 250


def _full_bleed(size):
    """A logo that fills its whole canvas: a 1 px frame plus content of another colour."""
    img = Image.new("RGBA", size, (10, 60, 140, 255))
    w, h = size
    ImageDraw.Draw(img).rectangle((1, 1, w - 2, h - 2), fill=(240, 120, 20, 255))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def test_a_huge_logo_is_scaled_down_keeping_its_shape():
    _, (w, h) = normalize_logo(_full_bleed((3000, 1000)))
    assert w <= MAX_WIDTH and h <= MAX_HEIGHT
    assert abs(w / h - 3.0) < 0.05


def test_a_small_but_fine_logo_is_not_enlarged():
    _, size = normalize_logo(_full_bleed((300, 100)))
    assert size == (300, 100)


@pytest.mark.parametrize(
    "raw, message",
    [
        (b"", "empty"),
        (b"not an image at all", "isn't an image"),
        (_image((150, 50), "white", mark_box=(10, 10, 140, 40)), r"too small \(150 × 50 px\)"),
        (_image((400, 200), (0, 0, 0, 0)), "fully transparent"),
        (_image((400, 200), "white"), "single plain colour"),
    ],
)
def test_bad_logos_are_refused_with_a_clear_reason(raw, message):
    with pytest.raises(LogoError, match=message):
        normalize_logo(raw)


def test_oversized_file_is_refused():
    with pytest.raises(LogoError, match="too large"):
        normalize_logo(b"x" * (5 * 1024 * 1024 + 1))
