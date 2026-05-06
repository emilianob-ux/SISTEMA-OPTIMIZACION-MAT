from __future__ import annotations

import numpy as np


def psi_histogram_score(reference: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """PSI aproximado con histogramas sobre límites compartidos (§4.1)."""
    ref = np.asarray(reference, dtype=float).ravel()
    act = np.asarray(actual, dtype=float).ravel()
    if ref.size == 0 or act.size == 0:
        raise ValueError("histogramas vacíos")

    merged = np.concatenate([ref, act])
    qs = np.quantile(merged, np.linspace(0.0, 1.0, bins + 1))
    qs[0] = float(np.min(merged))
    qs[-1] = float(np.max(merged))

    ref_hist, _ = np.histogram(ref, bins=qs)
    act_hist, _ = np.histogram(act, bins=qs)

    ref_p = ref_hist.astype(float) / max(ref.size, 1)
    act_p = act_hist.astype(float) / max(act.size, 1)
    eps = 1e-6
    return float(np.sum((act_p - ref_p) * np.log((act_p + eps) / (ref_p + eps))))


def frobenius_norm_diff(ref_sigma: np.ndarray, act_sigma: np.ndarray) -> float:
    a = np.asarray(ref_sigma, dtype=float)
    b = np.asarray(act_sigma, dtype=float)
    if a.shape != b.shape:
        raise ValueError("dimensiones distintas")
    return float(np.linalg.norm(a - b, ord="fro"))
