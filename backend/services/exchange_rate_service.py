"""Today's exchange-rate helper (scan date).

1 bill-currency unit in the region's base currency, taken from the public
currency-api snapshot for today — not typed by the employee.

If today's file is not published yet, walk back a few days.
"""

from datetime import date, timedelta
from typing import Any, Callable, Optional

import httpx

_URLS = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{day}/v1/currencies/{code}.min.json",
    "https://{day}.currency-api.pages.dev/v1/currencies/{code}.min.json",
)
_LOOKBACK_DAYS = 7

HttpGet = Callable[[str], Optional[dict[str, Any]]]

_cache: dict[tuple[str, str, str], dict[str, Any]] = {}


class ExchangeRateError(ValueError):
    pass


def clear_rate_cache() -> None:
    _cache.clear()


def lookup_rate(
    bill_currency: str,
    base_currency: str,
    _ignored_date: Optional[str] = None,
    *,
    fetch: Optional[HttpGet] = None,
    required: bool = True,
) -> dict[str, Any]:
    """Return {rate, as_of, bill_currency, base_currency, source} for today (scan date)."""
    bill = (bill_currency or "").strip().upper()
    base = (base_currency or "").strip().upper()
    if not bill or not base:
        raise ExchangeRateError("Bill currency and region currency are required")

    today = date.today()
    if bill == base:
        return {
            "rate": 1.0,
            "as_of": today.isoformat(),
            "bill_currency": bill,
            "base_currency": base,
            "source": "same_currency",
        }

    cache_key = (bill, base, today.isoformat())
    if fetch is None and cache_key in _cache:
        return dict(_cache[cache_key])

    getter = fetch or _http_get
    last_error: Optional[Exception] = None
    for offset in range(_LOOKBACK_DAYS + 1):
        day = today - timedelta(days=offset)
        try:
            rate = _fetch_pair(bill, base, day, getter)
        except Exception as exc:
            last_error = exc
            continue
        if rate and rate > 0:
            result = {
                "rate": round(float(rate), 6),
                "as_of": day.isoformat(),
                "bill_currency": bill,
                "base_currency": base,
                "source": "currency_api",
            }
            if fetch is None:
                _cache[cache_key] = result
            return dict(result)

    raise ExchangeRateError(
        f"Could not look up the {bill} to {base} rate for {today.isoformat()}"
    ) from last_error


def _fetch_pair(from_code: str, to_code: str, day: date, fetch: HttpGet) -> Optional[float]:
    src, dst = from_code.lower(), to_code.lower()
    iso = day.isoformat()
    for template in _URLS:
        payload = fetch(template.format(day=iso, code=src))
        if not payload:
            continue
        table = payload.get(src) or payload.get(from_code)
        if not isinstance(table, dict):
            continue
        raw = table.get(dst)
        if raw is None:
            raw = table.get(to_code)
        if raw is None:
            continue
        rate = float(raw)
        if rate > 0:
            return rate
    return None


def _http_get(url: str) -> Optional[dict[str, Any]]:
    try:
        resp = httpx.get(url, timeout=8.0, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None
