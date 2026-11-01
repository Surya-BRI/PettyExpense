"""Scan-date exchange-rate helper: today's rate, same-currency = 1."""

import os
from datetime import date, timedelta

for _k in ("READER_DB_SERVER", "READER_DB_NAME", "READER_DB_USER", "READER_DB_PASSWORD"):
    os.environ.setdefault(_k, "test")

import pytest  # noqa: E402

from services.exchange_rate_service import ExchangeRateError, lookup_rate  # noqa: E402


def test_same_currency_is_one():
    got = lookup_rate("AED", "AED")
    assert got["rate"] == 1.0
    assert got["source"] == "same_currency"
    assert got["as_of"] == date.today().isoformat()


def test_looks_up_todays_rate():
    today = date.today().isoformat()

    def fetch(url):
        assert today in url
        assert "/omr.min.json" in url
        return {"date": today, "omr": {"aed": 9.5412}}

    got = lookup_rate("OMR", "AED", fetch=fetch)
    assert got["rate"] == 9.5412
    assert got["as_of"] == today
    assert got["bill_currency"] == "OMR"
    assert got["base_currency"] == "AED"


def test_walks_back_when_today_has_no_snapshot():
    today = date.today()

    def fetch(url):
        if today.isoformat() in url:
            return None
        previous = today - timedelta(days=1)
        if previous.isoformat() in url:
            return {"date": previous.isoformat(), "usd": {"aed": 3.6725}}
        return None

    got = lookup_rate("USD", "AED", fetch=fetch)
    assert got["rate"] == 3.6725
    assert got["as_of"] == (today - timedelta(days=1)).isoformat()


def test_missing_pair_raises():
    def fetch(_url):
        return {"date": date.today().isoformat(), "usd": {}}

    with pytest.raises(ExchangeRateError, match="USD to AED"):
        lookup_rate("USD", "AED", fetch=fetch)
