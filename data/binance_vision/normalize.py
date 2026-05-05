"""Parseo de CSV dentro de zips y escritura de cache CSV normalizada."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

NORMALIZED_FUNDING_COLUMNS = (
    "symbol",
    "calc_time_ms",
    "funding_interval_hours",
    "funding_rate",
)

# Columnas alineadas con CSV de Binance Vision (klines suelen traer cabecera).
NORMALIZED_KLINE_COLUMNS = (
    "symbol",
    "open_time_ms",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_ms",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
)


def _read_csv_rows_from_zip(zip_bytes: bytes) -> Tuple[List[str], List[List[str]]]:
    """Devuelve (header, rows) leyendo el primer .csv del zip."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise ValueError("El zip no contiene ningun archivo .csv")
        name = sorted(names)[0]
        with zf.open(name, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            rows = list(reader)
    if not rows:
        return [], []
    header = [c.strip() for c in rows[0]]
    data_rows = rows[1:]
    return header, data_rows


def _is_probably_header(row: Sequence[str]) -> bool:
    if not row:
        return False
    first = row[0].lower()
    return first in ("open_time", "calc_time", "open time")


def normalize_funding_rows(
    symbol: str, header: List[str], data_rows: List[List[str]]
) -> Iterable[dict]:
    """Mapea filas de funding a dicts con esquema fijo."""
    idx = {h.lower(): i for i, h in enumerate(header)}
    need = ("calc_time", "funding_interval_hours", "last_funding_rate")
    if all(k in idx for k in need):
        for row in data_rows:
            if not row or all(not c.strip() for c in row):
                continue
            yield {
                "symbol": symbol.upper(),
                "calc_time_ms": int(row[idx["calc_time"]]),
                "funding_interval_hours": int(float(row[idx["funding_interval_hours"]])),
                "funding_rate": float(row[idx["last_funding_rate"]]),
            }
        return

    # Fallback: orden Binance tipico (sin cabecera reconocible).
    for row in data_rows:
        if not row or len(row) < 3:
            continue
        if _is_probably_header(row):
            continue
        yield {
            "symbol": symbol.upper(),
            "calc_time_ms": int(row[0]),
            "funding_interval_hours": int(float(row[1])),
            "funding_rate": float(row[2]),
        }


def normalize_kline_rows(
    symbol: str, header: List[str], data_rows: List[List[str]]
) -> Iterable[dict]:
    """Normaliza filas de klines a nombres de columna estables."""
    if header and _is_probably_header(header):
        idx = {h.lower().replace(" ", "_"): i for i, h in enumerate(header)}
        for row in data_rows:
            if not row or len(row) < 11:
                continue
            try:
                yield {
                    "symbol": symbol.upper(),
                    "open_time_ms": int(row[idx["open_time"]]),
                    "open": float(row[idx["open"]]),
                    "high": float(row[idx["high"]]),
                    "low": float(row[idx["low"]]),
                    "close": float(row[idx["close"]]),
                    "volume": float(row[idx["volume"]]),
                    "close_time_ms": int(row[idx["close_time"]]),
                    "quote_volume": float(row[idx["quote_volume"]]),
                    "trade_count": int(row[idx["count"]]),
                    "taker_buy_base_volume": float(row[idx["taker_buy_volume"]]),
                    "taker_buy_quote_volume": float(row[idx["taker_buy_quote_volume"]]),
                    "ignore": int(float(row[idx["ignore"]])) if row[idx["ignore"]] else 0,
                }
            except (ValueError, KeyError, IndexError):
                continue
        return

    for row in data_rows:
        if not row or len(row) < 11:
            continue
        if _is_probably_header(row):
            continue
        yield {
            "symbol": symbol.upper(),
            "open_time_ms": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "close_time_ms": int(row[6]),
            "quote_volume": float(row[7]),
            "trade_count": int(row[8]),
            "taker_buy_base_volume": float(row[9]),
            "taker_buy_quote_volume": float(row[10]),
            "ignore": int(float(row[11])) if len(row) > 11 and row[11] else 0,
        }


def write_funding_csv(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=NORMALIZED_FUNDING_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
            n += 1
    return n


def write_klines_csv(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=NORMALIZED_KLINE_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
            n += 1
    return n


def process_funding_zip(symbol: str, zip_bytes: bytes, out_csv: Path) -> int:
    header, data_rows = _read_csv_rows_from_zip(zip_bytes)
    rows = list(normalize_funding_rows(symbol, header, data_rows))
    return write_funding_csv(out_csv, rows)


def process_klines_zip(symbol: str, zip_bytes: bytes, out_csv: Path) -> int:
    header, data_rows = _read_csv_rows_from_zip(zip_bytes)
    rows = list(normalize_kline_rows(symbol, header, data_rows))
    return write_klines_csv(out_csv, rows)
