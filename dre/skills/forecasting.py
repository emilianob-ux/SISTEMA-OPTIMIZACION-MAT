from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
from scipy import stats


def fit_univariate_series(samples: np.ndarray) -> Dict[str, Any]:
    """Ajuste paramétrico simple + estadístico KS respecto a normal empírica (MVP §1.1)."""
    x = np.asarray(samples, dtype=float).ravel()
    n = int(x.size)
    if n == 0:
        raise ValueError("samples vacíos")

    mu = float(np.mean(x))
    sd = float(np.std(x, ddof=1)) if n > 1 else 0.0
    cv = float(sd / abs(mu)) if abs(mu) > 1e-12 else float("inf")

    ks_stat: Optional[float] = None
    ks_pvalue: Optional[float] = None
    if n > 5 and sd > 1e-12:
        ks_stat, ks_pvalue = stats.kstest(x, "norm", args=(mu, sd))

    return {
        "kind": "univariate_gaussian_proxy",
        "n": n,
        "mean": mu,
        "std": sd,
        "cv_effective": cv,
        "cv_source": "historical_proxy",
        "ks_statistic": ks_stat,
        "ks_pvalue": ks_pvalue,
    }
