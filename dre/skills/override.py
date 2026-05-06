from __future__ import annotations

from typing import Literal


def classify_override_delta_kpi(
    delta_kpi_pct: float,
) -> Literal["AUTO_APPROVE", "ELEVATED", "REJECT"]:
    """Sandbox ΔKPI §6.2 (percentiles relativos al KPI base)."""
    a = abs(delta_kpi_pct)
    if a <= 5.0:
        return "AUTO_APPROVE"
    if delta_kpi_pct >= -15.0:
        return "ELEVATED"
    return "REJECT"
