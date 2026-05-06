from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any, Dict, Literal

import numpy as np
from scipy.optimize import linprog

RelaxStatus = Literal["FEASIBLE", "INFEASIBLE", "TIMEOUT", "SOLVER_ERROR"]


def lp_relaxation_timboxed(
    c: np.ndarray,
    a_ub: np.ndarray,
    b_ub: np.ndarray,
    *,
    timeout_sec: float = 2.0,
) -> tuple[RelaxStatus, Dict[str, Any]]:
    """LP relajación pre-solver (§2.2), ejecutado en hilo con tope de tiempo.

    MVP: HiGHS (`scipy.optimize.linprog`). El stack objetivo incluye `cvxpy` para
    reformulaciones simbólicas de mayor nivel en iteraciones posteriores.
    """

    def _solve() -> RelaxStatus:
        res = linprog(
            np.asarray(c, dtype=float).ravel(),
            A_ub=np.asarray(a_ub, dtype=float),
            b_ub=np.asarray(b_ub, dtype=float).ravel(),
            bounds=(0, None),
            method="highs",
        )
        if res.success and res.status == 0:
            return "FEASIBLE"
        return "INFEASIBLE"

    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_solve)
        try:
            status = fut.result(timeout=timeout_sec)
            return status, {"solver": "scipy.highs"}
        except FuturesTimeout:
            return "TIMEOUT", {"reason": "concurrent_timeout"}
