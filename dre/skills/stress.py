from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
from scipy.optimize import linprog


@dataclass
class StressBatchResult:
    n_scenarios: int
    infeasibility_rate: float
    min_slack_global: float


def stress_lp_batch(
    c: np.ndarray,
    a_ub: np.ndarray,
    b_ub: np.ndarray,
    deltas: List[np.ndarray],
    *,
    tol_feas: float = 1e-9,
) -> StressBatchResult:
    """Mini stress determinístico: LP feasible Ax<=b+delta; slack mínimo global §1.2."""
    n_rows = int(a_ub.shape[0])
    infeas = 0
    min_slack = float("inf")
    for d in deltas:
        rhs = b_ub + np.asarray(d, dtype=float).ravel()
        if rhs.shape != (n_rows,):
            raise ValueError("delta incompatible con RHS")
        res = linprog(c, A_ub=a_ub, b_ub=rhs, bounds=(0, None), method="highs")
        ok = res.success and res.status == 0 and res.x is not None
        if not ok:
            infeas += 1
            continue
        slack = rhs - a_ub @ res.x
        min_slack = min(min_slack, float(np.min(slack)))
    n = len(deltas)
    rate = infeas / max(n, 1)
    if np.isinf(min_slack):
        min_slack = 0.0
    return StressBatchResult(
        n_scenarios=n,
        infeasibility_rate=float(rate),
        min_slack_global=float(min_slack),
    )
