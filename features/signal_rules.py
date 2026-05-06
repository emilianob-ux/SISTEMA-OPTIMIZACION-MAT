"""
Compila reglas JSON en máscaras booleanas por barra (True = permite operar long
junto al cóctel existente).
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from features.indicators import EMA_PERIODS


def _finite(x: float) -> bool:
    return bool(np.isfinite(x))


def apply_rules_to_pack(
    pack: dict[str, np.ndarray], rules: list[dict[str, Any]], logic: str
) -> np.ndarray:
    """
    logic: 'all' (AND) o 'any' (OR).
    Cada regla debe cumplirse en esa barra para pasar (AND) o al menos una (OR).
    Si una regla usa ADX y es NaN -> False (conservador).
    """
    n = len(next(iter(pack.values())))
    ok = np.ones(n, dtype=bool)
    per = []
    for rule in rules:
        op = rule.get("op")
        arr = np.ones(n, dtype=bool)
        if op == "adx_ge":
            thr = float(rule["value"])
            adx = pack["adx"]
            arr = np.isfinite(adx) & (adx >= thr)
        elif op == "adx_le":
            thr = float(rule["value"])
            adx = pack["adx"]
            arr = np.isfinite(adx) & (adx <= thr)
        elif op == "atr_pct_ge":
            thr = float(rule["value"])
            a = pack["atr_pct_close"]
            arr = np.isfinite(a) & (a >= thr)
        elif op == "atr_pct_le":
            thr = float(rule["value"])
            a = pack["atr_pct_close"]
            arr = np.isfinite(a) & (a <= thr)
        elif op == "bb_width_le":
            thr = float(rule["value"])
            w = pack["bb_width"]
            arr = np.isfinite(w) & (w <= thr)
        elif op == "bb_width_ge":
            thr = float(rule["value"])
            w = pack["bb_width"]
            arr = np.isfinite(w) & (w >= thr)
        elif op == "bb_pctb_ge":
            thr = float(rule["value"])
            b = pack["bb_pctb"]
            arr = np.isfinite(b) & (b >= thr)
        elif op == "bb_pctb_le":
            thr = float(rule["value"])
            b = pack["bb_pctb"]
            arr = np.isfinite(b) & (b <= thr)
        elif op == "dist_close_ema_ge":
            p = int(rule["ema_period"])
            if p not in EMA_PERIODS:
                raise ValueError(f"ema_period {p} no está en {EMA_PERIODS}")
            thr = float(rule["value_pct"])
            d = pack[f"dist_close_ema_{p}_pct"]
            arr = np.isfinite(d) & (d >= thr)
        elif op == "dist_close_ema_le":
            p = int(rule["ema_period"])
            if p not in EMA_PERIODS:
                raise ValueError(f"ema_period {p} no está en {EMA_PERIODS}")
            thr = float(rule["value_pct"])
            d = pack[f"dist_close_ema_{p}_pct"]
            arr = np.isfinite(d) & (d <= thr)
        elif op == "ema_spread_ge":
            a, b = int(rule["fast"]), int(rule["slow"])
            if a >= b or a not in EMA_PERIODS or b not in EMA_PERIODS:
                raise ValueError("ema_spread_ge requiere fast<slow en EMA_PERIODS")
            thr = float(rule["value_pct_on_close"])
            s = pack[f"ema_spread_{a}_{b}_pct_close"]
            arr = np.isfinite(s) & (s >= thr)
        elif op == "ema_spread_le":
            a, b = int(rule["fast"]), int(rule["slow"])
            if a >= b or a not in EMA_PERIODS or b not in EMA_PERIODS:
                raise ValueError("ema_spread_le requiere fast<slow en EMA_PERIODS")
            thr = float(rule["value_pct_on_close"])
            s = pack[f"ema_spread_{a}_{b}_pct_close"]
            arr = np.isfinite(s) & (s <= thr)
        elif op == "ema_cross_above":
            a, b = int(rule["fast"]), int(rule["slow"])
            if a >= b:
                raise ValueError("ema_cross_above: fast < slow")
            ea, eb = pack[f"ema_{a}"], pack[f"ema_{b}"]
            arr = np.isfinite(ea) & np.isfinite(eb) & (ea > eb)
        elif op == "ema_cross_below":
            a, b = int(rule["fast"]), int(rule["slow"])
            if a >= b:
                raise ValueError("ema_cross_below: fast < slow")
            ea, eb = pack[f"ema_{a}"], pack[f"ema_{b}"]
            arr = np.isfinite(ea) & np.isfinite(eb) & (ea < eb)
        elif op == "vol_ratio_ge":
            thr = float(rule["value"])
            v = pack["vol_ratio_vs_sma20"]
            arr = np.isfinite(v) & (v >= thr)
        elif op == "vol_ratio_le":
            thr = float(rule["value"])
            v = pack["vol_ratio_vs_sma20"]
            arr = np.isfinite(v) & (v <= thr)
        elif op == "vol_log_chg_ge":
            thr = float(rule["value"])
            v = pack["vol_log_chg_5"]
            arr = np.isfinite(v) & (v >= thr)
        elif op == "vol_log_chg_le":
            thr = float(rule["value"])
            v = pack["vol_log_chg_5"]
            arr = np.isfinite(v) & (v <= thr)
        else:
            raise ValueError(f"op desconocida: {op}")
        per.append(arr)

    if not per:
        return ok
    stacked = np.stack(per, axis=0)
    if logic == "any":
        return np.any(stacked, axis=0)
    return np.all(stacked, axis=0)


def load_signal_config(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if cfg.get("version", 1) != 1:
        raise ValueError("signal_config version != 1 no soportada")
    logic = str(cfg.get("logic", "all")).lower()
    if logic not in ("all", "any"):
        raise ValueError("logic debe ser 'all' o 'any'")
    rules = cfg.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("rules debe ser lista")
    return {"logic": logic, "rules": rules}


def masks_from_ohlcv(
    close: np.ndarray,
    high: np.ndarray | None,
    low: np.ndarray | None,
    volume: np.ndarray | None,
    cfg: dict[str, Any],
) -> np.ndarray:
    from features.indicators import compute_feature_pack

    pack = compute_feature_pack(close, high, low, volume)
    return apply_rules_to_pack(pack, cfg["rules"], cfg["logic"])
