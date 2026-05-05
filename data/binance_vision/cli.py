"""CLI: descarga desde data.binance.vision, parseo y cache CSV normalizada."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from data.binance_vision.dates import iter_days_spanning_months, iter_year_months
from data.binance_vision.download import download_bytes
from data.binance_vision.normalize import process_funding_zip, process_klines_zip
from data.binance_vision.urls import (
    funding_monthly_zip_url,
    klines_daily_zip_url,
    klines_monthly_zip_url,
)


def _default_cache_root() -> Path:
    # Repo root = parents[2] desde .../data/binance_vision/cli.py
    return Path(__file__).resolve().parents[2] / "data" / "cache" / "binance_vision"


def run(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Descarga datos publicos de Binance Vision (futures USD-M)."
    )
    p.add_argument(
        "--data-type",
        choices=("funding", "klines"),
        default="funding",
        help="Tipo de dataset (por defecto funding).",
    )
    p.add_argument("--symbol", default="BTCUSDT", help="Par futures, ej. BTCUSDT, ETHUSDT.")
    p.add_argument(
        "--interval",
        default="1m",
        help="Intervalo de velas (solo klines), ej. 1m, 5m, 1h.",
    )
    p.add_argument(
        "--granularity",
        choices=("monthly", "daily"),
        default="monthly",
        help="Zip mensual o diario (solo klines; funding siempre mensual).",
    )
    p.add_argument(
        "--start-month",
        required=True,
        help="Primer mes inclusive en formato YYYY-MM.",
    )
    p.add_argument(
        "--end-month",
        required=True,
        help="Ultimo mes inclusive en formato YYYY-MM.",
    )
    p.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Raiz de cache (por defecto <repo>/data/cache/binance_vision).",
    )
    args = p.parse_args(argv)

    cache_root = args.cache_dir or _default_cache_root()
    symbol = args.symbol.upper()
    session = requests.Session()

    if args.data_type == "funding":
        months = iter_year_months(args.start_month, args.end_month)
        for ym in months:
            url = funding_monthly_zip_url(symbol, ym)
            out = (
                cache_root
                / "futures_um"
                / "funding"
                / symbol
                / f"{symbol}_funding_{ym}.csv"
            )
            try:
                raw = download_bytes(url, session=session)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    print(f"[omitido] 404 {url}", file=sys.stderr)
                    continue
                raise
            n = process_funding_zip(symbol, raw, out)
            print(f"OK funding {symbol} {ym} -> {out} ({n} filas)")
        return 0

    if args.granularity == "monthly":
        periods = iter_year_months(args.start_month, args.end_month)
        for period in periods:
            url = klines_monthly_zip_url(symbol, args.interval, period)
            out = (
                cache_root
                / "futures_um"
                / "klines"
                / symbol
                / args.interval
                / f"{symbol}_{args.interval}_{period}.csv"
            )
            try:
                raw = download_bytes(url, session=session)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    print(f"[omitido] 404 {url}", file=sys.stderr)
                    continue
                raise
            n = process_klines_zip(symbol, raw, out)
            print(f"OK klines {symbol} {args.interval} {period} -> {out} ({n} filas)")
        return 0

    days = list(iter_days_spanning_months(args.start_month, args.end_month))
    for d in days:
        url = klines_daily_zip_url(symbol, args.interval, d)
        out = (
            cache_root
            / "futures_um"
            / "klines"
            / symbol
            / args.interval
            / "daily"
            / f"{symbol}_{args.interval}_{d}.csv"
        )
        try:
            raw = download_bytes(url, session=session)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                print(f"[omitido] 404 {url}", file=sys.stderr)
                continue
            raise
        n = process_klines_zip(symbol, raw, out)
        print(f"OK klines daily {symbol} {args.interval} {d} -> {out} ({n} filas)")
    return 0


def main() -> None:
    raise SystemExit(run())
