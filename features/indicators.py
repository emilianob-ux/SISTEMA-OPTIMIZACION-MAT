"""
Indicadores vectorizados en serie 5m (misma convención que compound_optimize_runner).

EMA 10/20/50/100/200 sobre close 5m.
ATR y ADX tipo Wilder si hay high/low; con solo close se usa ATR proxy y ADX no disponible (NaN).
Bollinger(20, 2) sobre close.
Cambio de volumen: ratio vs SMA(20) del volumen y retorno log en k barras.
"""

from __future__ import annotations

import numpy as np

EMA_PERIODS = (10, 20, 50, 100, 200)


def ema(close: np.ndarray, period: int) -> np.ndarray:
    n = len(close)
    out = np.zeros(n, dtype=np.float64)
    if n < period:
        return out
    out[period - 1] = np.mean(close[:period])
    k = 2.0 / (period + 1.0)
    for i in range(period, n):
        out[i] = close[i] * k + out[i - 1] * (1.0 - k)
    return out


def sma(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.zeros(n, dtype=np.float64)
    if n < period:
        return out
    c = np.cumsum(np.insert(x.astype(np.float64), 0, 0.0))
    out[period - 1 :] = (c[period:] - c[:-period]) / float(period)
    return out


def _wilder_smooth(x: np.ndarray, period: int) -> np.ndarray:
    """Wilder smoothing (RMA): primer valor = SMA, luego (prev*(p-1)+x)/p."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return out
    out[period - 1] = np.nanmean(x[:period])
    for i in range(period, n):
        v = x[i]
        if np.isnan(v):
            out[i] = out[i - 1]
        else:
            out[i] = (out[i - 1] * (period - 1) + v) / period
    return out


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    n = len(close)
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, hc, lc)
    return tr


def atr_wilder(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    tr = true_range(high, low, close)
    return _wilder_smooth(tr, period)


def atr_close_proxy(close: np.ndarray, period: int = 14) -> np.ndarray:
    """ATR aproximado solo con close: Wilder sobre |retorno simple|."""
    r = np.zeros_like(close, dtype=np.float64)
    r[1:] = np.abs(close[1:] - close[:-1])
    return _wilder_smooth(r, period)


def adx_wilder(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """ADX clásico [0,100]. Requiere high/low válidos."""
    n = len(close)
    plus_dm = np.zeros(n, dtype=np.float64)
    minus_dm = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        plus_dm[i] = up if up > down and up > 0 else 0.0
        minus_dm[i] = down if down > up and down > 0 else 0.0
    tr = true_range(high, low, close)
    atr_tr = _wilder_smooth(tr, period)
    sm_plus = _wilder_smooth(plus_dm, period)
    sm_minus = _wilder_smooth(minus_dm, period)
    eps = 1e-12
    plus_di = 100.0 * sm_plus / (atr_tr + eps)
    minus_di = 100.0 * sm_minus / (atr_tr + eps)
    dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di + eps)
    adx = _wilder_smooth(dx, period)
    return adx


def bollinger(close: np.ndarray, period: int = 20, num_std: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """mid, upper, lower, width=(u-l)/mid, pctb posición en banda [0,1] si mid>0."""
    mid = sma(close, period)
    n = len(close)
    std = np.zeros(n, dtype=np.float64)
    for i in range(period - 1, n):
        seg = close[i - period + 1 : i + 1]
        std[i] = float(np.std(seg, ddof=0))
    upper = mid + num_std * std
    lower = mid - num_std * std
    eps = 1e-12
    width = np.zeros(n, dtype=np.float64)
    pctb = np.zeros(n, dtype=np.float64)
    for i in range(n):
        if abs(mid[i]) > eps:
            width[i] = (upper[i] - lower[i]) / (mid[i] + eps)
        den = upper[i] - lower[i]
        if abs(den) > eps:
            pctb[i] = (close[i] - lower[i]) / den
    return mid, upper, lower, width, pctb


def volume_vs_sma_ratio(volume: np.ndarray, period: int = 20) -> np.ndarray:
    """vol / SMA(vol) - 1; NaN donde no hay historia."""
    v = volume.astype(np.float64)
    base = sma(v, period)
    out = np.full(len(v), np.nan, dtype=np.float64)
    m = base > 1e-12
    out[m] = v[m] / base[m] - 1.0
    return out


def volume_log_change(volume: np.ndarray, lag: int = 5) -> np.ndarray:
    """log(vol_t / vol_{t-lag}); volumen 0 -> NaN."""
    v = np.maximum(volume.astype(np.float64), 1e-12)
    out = np.full(len(v), np.nan, dtype=np.float64)
    out[lag:] = np.log(v[lag:] / v[:-lag])
    return out


def compute_feature_pack(
    close: np.ndarray,
    high: np.ndarray | None,
    low: np.ndarray | None,
    volume: np.ndarray | None,
    *,
    adx_period: int = 14,
    atr_period: int = 14,
    bb_period: int = 20,
    bb_std: float = 2.0,
    vol_sma: int = 20,
    vol_lag: int = 5,
) -> dict[str, np.ndarray]:
    """
    Devuelve dict de series alineadas a `close` (misma longitud).
    Claves estables para reglas e importancia.
    """
    n = len(close)
    c = close.astype(np.float64)
    pack: dict[str, np.ndarray] = {}

    for p in EMA_PERIODS:
        e = ema(c, p)
        pack[f"ema_{p}"] = e
        with np.errstate(divide="ignore", invalid="ignore"):
            pack[f"dist_close_ema_{p}_pct"] = np.where(e > 1e-12, (c - e) / e, np.nan)

    pairs = [(a, b) for a in EMA_PERIODS for b in EMA_PERIODS if a < b]
    for a, b in pairs:
        ea, eb = pack[f"ema_{a}"], pack[f"ema_{b}"]
        with np.errstate(divide="ignore", invalid="ignore"):
            pack[f"ema_spread_{a}_{b}_pct_close"] = np.where(c > 1e-12, (ea - eb) / c, np.nan)

    if high is not None and low is not None and not np.allclose(high, low):
        pack["atr"] = atr_wilder(high.astype(np.float64), low.astype(np.float64), c, atr_period)
        pack["adx"] = adx_wilder(high.astype(np.float64), low.astype(np.float64), c, adx_period)
    else:
        pack["atr"] = atr_close_proxy(c, atr_period)
        pack["adx"] = np.full(n, np.nan, dtype=np.float64)

    mid, upper, lower, width, pctb = bollinger(c, bb_period, bb_std)
    pack["bb_mid"] = mid
    pack["bb_upper"] = upper
    pack["bb_lower"] = lower
    pack["bb_width"] = width
    pack["bb_pctb"] = pctb

    if volume is not None and np.nanmax(volume) > 0:
        v = volume.astype(np.float64)
        pack["vol_ratio_vs_sma20"] = volume_vs_sma_ratio(v, vol_sma)
        pack["vol_log_chg_5"] = volume_log_change(v, vol_lag)
    else:
        pack["vol_ratio_vs_sma20"] = np.zeros(n, dtype=np.float64)
        pack["vol_log_chg_5"] = np.zeros(n, dtype=np.float64)

    with np.errstate(divide="ignore", invalid="ignore"):
        pack["atr_pct_close"] = np.where(c > 1e-12, pack["atr"] / c, np.nan)

    return pack


def feature_matrix_at_index(pack: dict[str, np.ndarray], idx: int) -> dict[str, float]:
    row: dict[str, float] = {}
    for k, arr in pack.items():
        if idx < 0 or idx >= len(arr):
            row[k] = float("nan")
        else:
            v = arr[idx]
            row[k] = float(v) if np.isfinite(v) else float("nan")
    return row


def column_names_for_importance() -> list[str]:
    """Subconjunto interpretable (sin duplicar todas las ema crudas si no hace falta)."""
    names: list[str] = []
    for p in EMA_PERIODS:
        names.append(f"dist_close_ema_{p}_pct")
    for a in EMA_PERIODS:
        for b in EMA_PERIODS:
            if a >= b:
                continue
            names.append(f"ema_spread_{a}_{b}_pct_close")
    names.extend(
        [
            "adx",
            "atr_pct_close",
            "bb_width",
            "bb_pctb",
            "vol_ratio_vs_sma20",
            "vol_log_chg_5",
        ]
    )
    return names


def pack_to_matrix(pack: dict[str, np.ndarray], indices: np.ndarray, colnames: list[str]) -> np.ndarray:
    """Shape (len(indices), len(colnames)); NaN -> 0.0 para regresión."""
    m = len(indices)
    d = len(colnames)
    X = np.zeros((m, d), dtype=np.float64)
    for j, name in enumerate(colnames):
        col = pack.get(name)
        if col is None:
            continue
        for r, i in enumerate(indices):
            if 0 <= i < len(col):
                v = col[i]
                X[r, j] = float(v) if np.isfinite(v) else 0.0
    return X
