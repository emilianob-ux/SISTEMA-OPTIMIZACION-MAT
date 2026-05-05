"""Utilidades de calendario (solo stdlib) para rangos mensuales/diarios."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Iterator, List, Tuple


def _parse_ym(s: str) -> Tuple[int, int]:
    parts = s.strip().split("-")
    if len(parts) != 2:
        raise ValueError(f"Mes invalido (use YYYY-MM): {s!r}")
    y, m = int(parts[0]), int(parts[1])
    if not (1 <= m <= 12):
        raise ValueError(f"Mes fuera de rango: {s!r}")
    return y, m


def iter_year_months(start_month: str, end_month: str) -> List[str]:
    """Inclusive. YYYY-MM strings."""
    y1, m1 = _parse_ym(start_month)
    y2, m2 = _parse_ym(end_month)
    if (y1, m1) > (y2, m2):
        raise ValueError("start_month debe ser <= end_month")
    out: List[str] = []
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def iter_days_spanning_months(start_month: str, end_month: str) -> Iterator[str]:
    """Dias calendario desde el dia 1 de start_month hasta el ultimo de end_month."""
    y1, m1 = _parse_ym(start_month)
    y2, m2 = _parse_ym(end_month)
    if (y1, m1) > (y2, m2):
        raise ValueError("start_month debe ser <= end_month")
    start = date(y1, m1, 1)
    last_day = calendar.monthrange(y2, m2)[1]
    end = date(y2, m2, last_day)
    d = start
    while d <= end:
        yield d.isoformat()
        d += timedelta(days=1)
