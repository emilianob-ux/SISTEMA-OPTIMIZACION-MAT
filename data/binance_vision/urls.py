"""Construccion de URLs estables para data.binance.vision (futures USD-M)."""

from __future__ import annotations

BASE_HOST = "https://data.binance.vision"


def funding_monthly_zip_url(symbol: str, year_month: str) -> str:
    """
    year_month: YYYY-MM (ej. 2024-01).

    Patron:
    /data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY-MM}.zip
    """
    s = symbol.upper()
    return (
        f"{BASE_HOST}/data/futures/um/monthly/fundingRate/"
        f"{s}/{s}-fundingRate-{year_month}.zip"
    )


def klines_monthly_zip_url(symbol: str, interval: str, year_month: str) -> str:
    """
    interval: ej. 1m, 5m, 1h.

    Patron:
    /data/futures/um/monthly/klines/{SYMBOL}/{interval}/{SYMBOL}-{interval}-{YYYY-MM}.zip
    """
    s = symbol.upper()
    iv = interval
    return (
        f"{BASE_HOST}/data/futures/um/monthly/klines/{s}/{iv}/"
        f"{s}-{iv}-{year_month}.zip"
    )


def klines_daily_zip_url(symbol: str, interval: str, year_month_day: str) -> str:
    """
    year_month_day: YYYY-MM-DD.

    Patron:
    /data/futures/um/daily/klines/{SYMBOL}/{interval}/{SYMBOL}-{interval}-{YYYY-MM-DD}.zip
    """
    s = symbol.upper()
    iv = interval
    return (
        f"{BASE_HOST}/data/futures/um/daily/klines/{s}/{iv}/"
        f"{s}-{iv}-{year_month_day}.zip"
    )
