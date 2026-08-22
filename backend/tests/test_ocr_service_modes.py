"""Unit tests for the OCR mode-selection contract in services/ocr_service.py, using fake engines (3 identifiable regions at x0=0/1/2) so tests run fast and can verify bbox/reading_order survive filtering — without downloading real ONNX models."""
import sys
from types import SimpleNamespace

import numpy as np
import pytest

# services/__init__.py shadows the submodule name with the OcrService instance, so `from services import ocr_service` would bind the wrong thing — go via sys.modules instead.
import services.ocr_service  # noqa: F401  (forces the module import below)

ocr_service = sys.modules["services.ocr_service"]

_NUM_REGIONS = 3


class _FakeEngine:
    # `region_results`, if given, is {region_index: (text, score)}, indexed back to the original region via `crop_index` (shared across en/ar).

    def __init__(self, tag: str, crop_index: dict, region_results: dict | None = None):
        self.tag = tag
        self.crop_index = crop_index
        self.region_results = region_results or {}
        self.recognize_calls = 0
        self.last_recognize_crop_count = None

    def load_img(self, image_bytes):
        return np.zeros((10, 10, 3), dtype=np.uint8)

    def preprocess_img(self, img):
        return img, {"preprocess": {"ratio_h": 1.0, "ratio_w": 1.0}}

    def detect_and_crop(self, img, op_record):
        boxes = np.array(
            [[[float(i), 0.0], [float(i) + 1, 0.0], [float(i) + 1, 1.0], [float(i), 1.0]] for i in range(_NUM_REGIONS)],
            dtype=np.float64,
        )
        crops = [np.full((2, 2, 3), i, dtype=np.uint8) for i in range(_NUM_REGIONS)]
        self.crop_index.update({id(c): i for i, c in enumerate(crops)})
        det_res = SimpleNamespace(boxes=boxes)
        return crops, det_res

    def recognize_txt(self, crops):
        self.recognize_calls += 1
        self.last_recognize_crop_count = len(crops)
        txts, scores = [], []
        for c in crops:
            idx = self.crop_index.get(id(c))
            text, score = self.region_results.get(idx, (f"{self.tag}-{idx}", 0.95))
            txts.append(text)
            scores.append(score)
        return SimpleNamespace(txts=txts, scores=scores)


def _make_engines(monkeypatch, en_region_results=None, ar_region_results=None):
    crop_index: dict = {}
    engines = {
        "en": _FakeEngine("en", crop_index, en_region_results),
        "ar": _FakeEngine("ar", crop_index, ar_region_results),
    }
    monkeypatch.setattr(ocr_service, "_get_rapid_engine", lambda lang: engines[lang])
    return engines


def test_english_mode_never_invokes_the_arabic_engine(monkeypatch):
    engines = _make_engines(monkeypatch)
    en_words, ar_words = ocr_service._run_shared_detection_ocr(b"fake-image-bytes", "en")
    assert engines["en"].recognize_calls == 1
    assert engines["ar"].recognize_calls == 0
    assert len(en_words) == _NUM_REGIONS
    assert ar_words == []


def test_arabic_mode_reads_every_region_unconditionally(monkeypatch):
    # Even a cleanly-read region must still get an Arabic reading in "ar" mode — Arabic is the PRIMARY reading here, never filtered.
    en_results = {0: ("Clean printed text", 0.99), 1: ("Also clean", 0.98), 2: ("Still clean", 0.99)}
    engines = _make_engines(monkeypatch, en_region_results=en_results)
    en_words, ar_words = ocr_service._run_shared_detection_ocr(b"fake-image-bytes", "ar")
    assert engines["en"].recognize_calls == 1
    assert engines["ar"].recognize_calls == 1
    assert engines["ar"].last_recognize_crop_count == _NUM_REGIONS
    assert len(ar_words) == _NUM_REGIONS


def test_auto_mode_retries_only_unreliable_regions(monkeypatch):
    en_results = {
        0: ("ENOC RETAIL", 0.99),      # clean — must NOT be retried
        1: ("kiagdomp toner", 0.50),   # low confidence — retry
        2: ("ركة شمل الدوحة", 0.95),    # high score but non-Latin-dominant — retry anyway
    }
    engines = _make_engines(monkeypatch, en_region_results=en_results)
    en_words, ar_words = ocr_service._run_shared_detection_ocr(b"fake-image-bytes", "auto")
    assert engines["en"].recognize_calls == 1
    assert engines["ar"].recognize_calls == 1
    assert engines["ar"].last_recognize_crop_count == 2  # only regions 1 and 2
    assert len(ar_words) == 2


def test_auto_mode_never_invokes_arabic_engine_when_every_region_is_clean(monkeypatch):
    en_results = {0: ("ENOC RETAIL", 0.99), 1: ("Tax Invoice", 0.98), 2: ("LLC", 0.99)}
    engines = _make_engines(monkeypatch, en_region_results=en_results)
    en_words, ar_words = ocr_service._run_shared_detection_ocr(b"fake-image-bytes", "auto")
    assert engines["en"].recognize_calls == 1
    assert engines["ar"].recognize_calls == 0  # never even constructed/invoked
    assert ar_words == []


def test_auto_mode_retry_preserves_original_bbox_and_reading_order(monkeypatch):
    # Region 2 is the only one retried — its word must keep region 2's own bbox/reading_order (x0==2.0), not the filtered subset's local position (0.0).
    en_results = {0: ("ENOC RETAIL", 0.99), 1: ("Tax Invoice", 0.98), 2: ("kiagdomp", 0.40)}
    ar_results = {2: ("قمة الخليج", 0.90)}
    engines = _make_engines(monkeypatch, en_region_results=en_results, ar_region_results=ar_results)
    en_words, ar_words = ocr_service._run_shared_detection_ocr(b"fake-image-bytes", "auto")
    assert engines["ar"].last_recognize_crop_count == 1
    assert len(ar_words) == 1
    word = ar_words[0]
    assert word.text == "قمة الخليج"
    assert word.reading_order == 2
    assert word.bounding_box is not None
    assert word.bounding_box[0] == pytest.approx(2.0)  # region 2's own x0, not 0.0


def test_detection_runs_exactly_once_regardless_of_mode(monkeypatch):
    engines = _make_engines(monkeypatch, en_region_results={1: ("low", 0.4)})
    calls = {"count": 0}
    original = engines["en"].detect_and_crop

    def counting_detect_and_crop(img, op_record):
        calls["count"] += 1
        return original(img, op_record)

    monkeypatch.setattr(engines["en"], "detect_and_crop", counting_detect_and_crop)
    ocr_service._run_shared_detection_ocr(b"fake-image-bytes", "auto")
    assert calls["count"] == 1


@pytest.mark.parametrize("raw_mode, expected", [("AUTO", "auto"), ("En", "en"), ("ar", "ar"), ("bogus", "auto"), (None, "auto")])
def test_normalize_mode_defaults_safely(raw_mode, expected):
    assert ocr_service._normalize_mode(raw_mode) == expected


@pytest.mark.parametrize(
    "text, score, expected",
    [
        ("ENOC RETAIL", 0.99, False),
        ("", 0.0, True),
        ("   ", 0.5, True),
        ("kiagdomp toner", 0.5, True),
        ("ركة شمل الدوحة", 0.95, True),
        ("Clean printed text", 0.93, False),
        ("Borderline", 0.90, False),  # exactly at threshold — not below it
        ("Borderline", 0.8999, True),
    ],
)
def test_needs_arabic_retry_rule(text, score, expected):
    assert ocr_service._needs_arabic_retry(text, score) is expected
