from __future__ import annotations

from typing import Literal

import numpy as np


def propensity_overlap_1d(treated: np.ndarray, control: np.ndarray, bins: int = 20) -> float:
    """Overlap tipo proporción de masa histogramática compartida [0,1] (proxy rápido §3)."""
    t = np.asarray(treated, dtype=float).ravel()
    c = np.asarray(control, dtype=float).ravel()
    merged = np.concatenate([t, c])
    lo, hi = float(np.min(merged)), float(np.max(merged))
    if hi - lo < 1e-12:
        return 1.0

    ht, edges = np.histogram(t, bins=bins, range=(lo, hi), density=True)
    hc, _ = np.histogram(c, bins=bins, range=(lo, hi), density=True)
    width = (edges[1] - edges[0]) if len(edges) > 1 else 1.0
    overlap_mass = np.sum(np.minimum(ht, hc)) * width
    return float(min(max(overlap_mass, 0.0), 1.0))


def tier1_gate(overlap: float, threshold: float = 0.6) -> Literal["PASS", "BLOCKED"]:
    return "PASS" if overlap >= threshold else "BLOCKED"
