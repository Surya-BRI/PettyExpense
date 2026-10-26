"""Unit tests for the GPT scan pipeline (services/llm_vision_service.py) -- OpenAI is never called;
httpx.post is replaced with canned responses shaped like real gpt-5.4-mini answers from the benchmark."""
import io
import json
import sys
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image

import services.llm_vision_service  # noqa: F401  (services/__init__ shadows submodule names; go via sys.modules)

llm = sys.modules["services.llm_vision_service"]
ocr_service_module = sys.modules["services.ocr_service"]
_json = json  # the fake httpx.post below takes a `json=` kwarg, which shadows the module


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buf, format="PNG")
    return buf.getvalue()


def _answer(**overrides) -> dict:
    # Pre-VAT rows with 5% per line, like new_bills/bill_3.png (Jannat Al Naeem tax invoice), first 2 rows.
    base = {
        "vendor": "Jannat Al Naeem Building Materials Trading LLC",
        "date": "2026-07-21",
        "amount": 1895.50,
        "vat_amount": 94.78,
        "vat_percent": 5,
        "total_amount": 1990.28,
        "currency": "AED",
        "bill_number": "19578",
        "line_items": [
            {"description": "Bolt 36X150", "quantity": 34, "amount": 697.00, "vat_percent": 5},
            {"description": "Bolt 30X120", "quantity": 102, "amount": 1198.50, "vat_percent": 5},
        ],
        "line_items_include_vat": False,
        "confidence": {"vendor": 0.95, "date": 0.9, "amount": 0.9, "vat_amount": 0.9,
                       "total_amount": 0.95, "currency": 0.9, "bill_number": 0.9},
        "notes": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def fake_openai(monkeypatch):
    calls = []

    def install(answer=None, status=200, exc=None, api_key="sk-test", provider="openai", runpod_endpoint="vlm123"):
        monkeypatch.setattr(llm, "get_settings", lambda: SimpleNamespace(
            ai_vision_provider=provider,
            openai_api_key=api_key, openai_vision_model="gpt-5.4-mini",
            openai_reasoning_effort="low", openai_timeout_seconds=60,
            runpod_api_key="rp-old-ocr-key", runpod_vision_api_key="rp-test", runpod_vision_endpoint_id=runpod_endpoint,
            runpod_vision_model="Qwen/Qwen3-VL-8B-Instruct", runpod_vision_timeout_seconds=300,
        ))

        def post(url, json=None, headers=None, timeout=None):  # noqa: A002 - mirrors httpx.post
            calls.append(dict(json, _url=url, _auth=headers["Authorization"], _timeout=timeout))
            if exc:
                raise exc
            body = {"model": "gpt-5.4-mini", "usage": {"prompt_tokens": 1500, "completion_tokens": 400},
                    "choices": [{"message": {"content": _json.dumps(answer)}}]} if status == 200 else {"error": "x"}
            return httpx.Response(status, json=body)

        monkeypatch.setattr(llm.httpx, "post", post)
        return calls

    return install


def test_maps_answer_to_ocr_service_shape(fake_openai):
    calls = fake_openai(_answer())
    r = llm.run_llm_vision(_png_bytes(), region_code="UAE")

    assert (r["vendor"], r["amount"], r["vat_amount"], r["total_amount"]) == (
        "Jannat Al Naeem Building Materials Trading LLC", 1895.5, 94.78, 1990.28)
    assert r["date"] == "2026-07-21" and r["currency"] == "AED"
    assert r["fields"]["invoice_number"]["value"] == "19578"  # what _receipt_payload reads as bill_number
    assert r["low_confidence_fields"] == [] and r["reconciliation_mismatch"] is False
    assert r["raw_json"]["engine"] == "openai_vision" and r["raw_json"]["usage"]["prompt_tokens"] == 1500
    # Sent as an image with the strict schema and reasoning effort from settings.
    sent = calls[0]
    assert sent["_url"] == "https://api.openai.com/v1/chat/completions" and sent["_auth"] == "Bearer sk-test"
    assert sent["model"] == "gpt-5.4-mini" and sent["reasoning_effort"] == "low"
    assert sent["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert sent["response_format"]["json_schema"]["strict"] is True


def test_runpod_provider_uses_the_vllm_endpoint_same_prompt_and_schema(fake_openai):
    calls = fake_openai(_answer(), provider="runpod")
    r = llm.run_llm_vision(_png_bytes(), region_code="UAE")

    sent = calls[0]
    assert sent["_url"] == "https://api.runpod.ai/v2/vlm123/openai/v1/chat/completions"
    assert sent["_auth"] == "Bearer rp-test" and sent["_timeout"] == 300
    assert sent["model"] == "Qwen/Qwen3-VL-8B-Instruct" and "reasoning_effort" not in sent
    assert sent["messages"][0]["content"] == llm.PROMPT and sent["response_format"]["json_schema"]["schema"] == llm.SCHEMA
    assert r["total_amount"] == 1990.28 and r["raw_json"]["provider"] == "runpod"


def test_runpod_provider_without_endpoint_raises_before_any_call(fake_openai):
    calls = fake_openai(_answer(), provider="runpod", runpod_endpoint="")
    with pytest.raises(llm.LlmVisionError, match="not set up"):
        llm.run_llm_vision(_png_bytes())
    assert calls == []


def test_pre_vat_rows_become_vat_inclusive_and_sum_to_total(fake_openai):
    fake_openai(_answer())
    lines = llm.run_llm_vision(_png_bytes(), region_code="UAE")["line_items"]

    # _replace_line_items sets total = sum(line amounts), so lines must be VAT-inclusive.
    assert [li["amount"] for li in lines] == [731.85, 1258.43]
    assert round(sum(li["amount"] for li in lines), 2) == 1990.28
    assert set(lines[0]) == {"description", "quantity", "amount", "confidence", "vat_percent"}  # OcrLineItem keys


def test_rows_already_summing_to_total_are_not_given_vat_again(fake_openai):
    # mage.png (Bab Al Hayat): "Net Total" column already includes VAT + discount, but the model
    # flagged include_vat=False. Rows 27.15 + 22.81(5%) + 390.03 = 439.99 vs bill total 440.00.
    rows = [
        {"description": "MED ADVANCE WOUND ADHESIVE 100S", "quantity": 2, "amount": 27.15, "vat_percent": 0},
        {"description": "ADV MED GUIDANCE CARD (FIRST AID BOOK)", "quantity": 3, "amount": 22.81, "vat_percent": 5},
        {"description": "MED DISPOSIBLE SYRINGE 20ML 50S", "quantity": 4, "amount": 390.03, "vat_percent": 0},
    ]
    fake_openai(_answer(amount=438.91, vat_amount=1.09, total_amount=440.0, line_items=rows))
    lines = llm.run_llm_vision(_png_bytes(), region_code="UAE")["line_items"]
    assert [li["amount"] for li in lines] == [27.15, 22.81, 390.04]  # only the 0.01 rounding absorbed
    assert round(sum(li["amount"] for li in lines), 2) == 440.0


def test_arithmetic_beats_the_models_include_vat_flag(fake_openai):
    # Rows sum to the pre-VAT amount (1895.50), so VAT is added even though the flag claims "inclusive".
    fake_openai(_answer(line_items_include_vat=True))
    lines = llm.run_llm_vision(_png_bytes(), region_code="UAE")["line_items"]
    assert [li["amount"] for li in lines] == [731.85, 1258.43]


def test_unsure_currency_falls_back_to_region(fake_openai):
    # ksa1.png: company named "Sharjah" made the model guess AED on a Saudi riyal slip.
    conf = dict(_answer()["confidence"], currency=0.3)
    fake_openai(_answer(currency="AED", confidence=conf, line_items=[], vat_amount=0, amount=45, total_amount=45))
    assert llm.run_llm_vision(_png_bytes(), region_code="KSA")["currency"] == "SAR"


def test_missing_total_is_derived_and_low_fields_flagged(fake_openai):
    conf = dict(_answer()["confidence"], date=0.4)
    fake_openai(_answer(total_amount=None, date=None, confidence=conf, line_items=[]))
    r = llm.run_llm_vision(_png_bytes(), region_code="UAE")
    assert r["total_amount"] == 1990.28
    assert r["date"] == "" and "date" in r["low_confidence_fields"]


def test_missing_key_raises_without_calling_openai(fake_openai):
    calls = fake_openai(_answer(), api_key="")
    with pytest.raises(llm.LlmVisionError, match="not set up"):
        llm.run_llm_vision(_png_bytes())
    assert calls == []


@pytest.mark.parametrize("status, message", [(401, "not authorised"), (429, "busy"), (500, "Scan failed")])
def test_http_errors_become_readable_errors(fake_openai, status, message):
    fake_openai(status=status)
    with pytest.raises(llm.LlmVisionError, match=message):
        llm.run_llm_vision(_png_bytes())


def test_timeout_becomes_readable_error(fake_openai):
    fake_openai(exc=httpx.ReadTimeout("slow"))
    with pytest.raises(llm.LlmVisionError, match="timed out"):
        llm.run_llm_vision(_png_bytes())


def test_unreadable_image_is_rejected_before_any_call(fake_openai):
    calls = fake_openai(_answer())
    with pytest.raises(llm.LlmVisionError, match="could not be opened"):
        llm.run_llm_vision(b"not an image")
    assert calls == []


def test_ocr_service_always_uses_gpt_without_fallback(monkeypatch):
    monkeypatch.setattr(ocr_service_module, "run_llm_vision", lambda b, region: {"engine": "ai", "region": region})
    monkeypatch.setattr(ocr_service_module, "_run_ocr", lambda *a, **k: pytest.fail("standard pipeline must not run"))
    assert ocr_service_module.OcrService().run(b"x", region_code="KSA") == {"engine": "ai", "region": "KSA"}
    # Older clients that still send engine=standard must still hit GPT.
    assert ocr_service_module.OcrService().run(b"x", engine="standard", region_code="KSA") == {"engine": "ai", "region": "KSA"}

    def boom(b, region):
        raise llm.LlmVisionError("AI scan timed out.")

    monkeypatch.setattr(ocr_service_module, "run_llm_vision", boom)
    with pytest.raises(llm.LlmVisionError):
        ocr_service_module.OcrService().run(b"x")
