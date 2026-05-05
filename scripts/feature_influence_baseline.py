"""
Influencia aproximada de features (sin tocar el cóctel): regresión ridge sobre etiqueta WIN
por ventana, usando features del activo BTC en la barra global s+lb (inicio útil del loop).

Advertencia: correlación / coeficientes lineales no implican causalidad ni ganancia OOS;
sirve para priorizar qué features explorar en reglas --signal-config.

Uso:
  python scripts/feature_influence_baseline.py --db data/candles.db
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from compound_optimize_runner import (  # noqa: E402
    calc_indicators,
    load_data,
    sim_window,
)
from features.indicators import column_names_for_importance, compute_feature_pack, pack_to_matrix  # noqa: E402
from features.loaders import load_btc_eth_series  # noqa: E402


def _ridge_coeffs(X: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    """y ~ X (sin intercepto en X ya centrado). Coeficientes mínimos cuadrados ridge."""
    n, d = X.shape
    XtX = X.T @ X
    A = XtX + lam * np.eye(d)
    b = X.T @ y
    return np.linalg.solve(A, b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=5.0)
    ap.add_argument("--max-windows", type=int, default=0, help="0 = todas")
    args = ap.parse_args()

    db = os.path.abspath(args.db)
    cl_b, cl_e, fcost_b, fcost_e = load_data(db)
    ema_b, sma_b = calc_indicators(cl_b)
    ema_e, sma_e = calc_indicators(cl_e)
    _c1, _c2, hi_b, lo_b, vo_b, hi_e, lo_e, vo_e = load_btc_eth_series(db)
    n = len(cl_b)
    hi_b = hi_b[:n] if hi_b is not None else None
    lo_b = lo_b[:n] if lo_b is not None else None
    vo_b = vo_b[:n] if vo_b is not None else None

    pack_b = compute_feature_pack(cl_b, hi_b, lo_b, vo_b)
    colnames = column_names_for_importance()

    w = 17280
    step = 288
    lb = 14 * 288
    nw = (n - w) // step + 1
    if args.max_windows > 0:
        nw = min(nw, args.max_windows)

    indices = np.array([ww * step + lb for ww in range(nw)], dtype=np.int64)
    X = pack_to_matrix(pack_b, indices, colnames)
    y = np.zeros(nw, dtype=np.float64)
    for ww in range(nw):
        s = ww * step
        e = s + w
        res, *_ = sim_window(
            cl_b[s:e],
            cl_e[s:e],
            fcost_b[s:e],
            fcost_e[s:e],
            ema_b[s:e],
            sma_b[s:e],
            ema_e[s:e],
            sma_e[s:e],
        )
        y[ww] = 1.0 if res == "WIN" else 0.0

    Xn = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    beta = _ridge_coeffs(Xn, y, args.lam)
    corr = []
    for j in range(X.shape[1]):
        c = np.corrcoef(Xn[:, j], y)[0, 1]
        corr.append(float(c) if np.isfinite(c) else 0.0)

    order = np.argsort(-np.abs(beta))
    ranked = [
        {"feature": colnames[j], "ridge_beta": float(beta[j]), "corr_y": corr[j]} for j in order[:25]
    ]
    out = {
        "n_windows": nw,
        "lambda": args.lam,
        "note": "Features en barra BTC s+lb; etiqueta WIN cóctel baseline sin --signal-config.",
        "top_by_abs_ridge_beta": ranked,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
