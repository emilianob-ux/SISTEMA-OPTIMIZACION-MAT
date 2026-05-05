"""
Control de apalancamiento PI + referencia feedforward (spec 2026-04-27).
Funciones puras; sin dependencias fuera de la stdlib.
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, Mapping, Optional, Tuple


def _sigmoid(x: float) -> float:
    if x >= 35.0:
        return 1.0
    if x <= -35.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def feedforward_L(E: float, cfg: Mapping[str, Any]) -> float:
    """L^ff(E): dos sigmoides (spec §4), clamp a [L_min, L_max]."""
    ff = cfg["L_ff"]
    hard = cfg["hard"]
    L_low = float(ff["L_low"])
    L_mid = float(ff["L_mid"])
    L_high = float(ff["L_high"])
    E_a = float(ff["E_a"])
    E_b = float(ff["E_b"])
    w_a = float(ff["w_a"])
    w_b = float(ff["w_b"])
    lo = float(hard["L_min"])
    hi = float(hard["L_max"])
    if w_a <= 0 or w_b <= 0:
        raise ValueError("w_a y w_b deben ser > 0")

    x_a = (float(E) - E_a) / w_a
    s_a = _sigmoid(x_a)
    l1 = L_low + (L_mid - L_low) * s_a
    x_b = (float(E) - E_b) / w_b
    s_b = _sigmoid(x_b)
    l_ff = l1 + (L_high - L_mid) * s_b
    return max(lo, min(hi, l_ff))


def error_e(E: float, cfg: Mapping[str, Any]) -> float:
    """Error dual (spec §5): e=0 si E < S_mode; si no, log(T_goal) - log(E)."""
    eps = float(cfg.get("eps", 1e-6))
    s_mode = float(cfg["S_mode"])
    if float(E) < s_mode:
        return 0.0
    t_goal = float(cfg["T_goal"])
    return math.log(max(t_goal, eps)) - math.log(max(float(E), eps))


def leverage_pi_step(E: float, I_prev: float, cfg: Mapping[str, Any]) -> Tuple[float, float]:
    """
    Un paso de decisión semanal: (L_k, I_{k+1}).
    Anti-windup: si L_prop sale de [L_min, L_max], I_next = I_prev (congelación, spec §6).
    Cuantización: round(L_float) con L_float clampado; L >= 1.
    """
    dt = float(cfg.get("dt_eff", 1.0))
    pi = cfg["pi"]
    k_p = float(pi["K_p"])
    k_i = float(pi["K_i"])
    i_max = float(pi["I_max"])
    hard = cfg["hard"]
    l_min = float(hard["L_min"])
    l_max = float(hard["L_max"])

    l_ff = feedforward_L(E, cfg)
    e_k = error_e(E, cfg)

    i_cand = I_prev + e_k * dt
    u_raw = k_p * e_k + k_i * i_cand
    l_prop = l_ff + u_raw

    if l_prop > l_max:
        l_applied = l_max
        i_next = I_prev
    elif l_prop < l_min:
        l_applied = l_min
        i_next = I_prev
    else:
        l_float = max(l_min, min(l_max, l_prop))
        i_next = max(-i_max, min(i_max, i_cand))
        l_q = round(l_float)
        if l_q < 1:
            l_q = 1
        l_applied = float(l_q)

    return l_applied, i_next


def default_pi_ref_config(t_goal: float = 1000.0) -> Dict[str, Any]:
    """Valores por defecto alineados al YAML de la spec (T_goal se sobrescribe con --target-equity)."""
    out: Dict[str, Any] = {
        "S_mode": 250.0,
        "T_goal": float(t_goal),
        "eps": 1e-6,
        "dt_eff": 1.0,
        "L_ff": {
            "L_low": 5.0,
            "L_mid": 8.0,
            "L_high": 10.0,
            "E_a": 220.0,
            "E_b": 280.0,
            "w_a": 15.0,
            "w_b": 15.0,
        },
        "hard": {"L_min": 3.0, "L_max": 12.0},
        "pi": {
            "K_p": 0.25,
            "K_i": 0.05,
            "I_max": 2.0,
            "anti_windup": "conditional_freeze",
        },
    }
    validate_pi_ref_config(out)
    return out


def load_pi_ref_config(path: str, t_goal_override: Optional[float] = None) -> Dict[str, Any]:
    """Carga JSON (misma forma que el bloque pi_ref de la spec)."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("Config PI: raíz debe ser un objeto JSON")
    inner = raw.get("pi_ref")
    if isinstance(inner, dict):
        raw = inner
    base = default_pi_ref_config()
    merged = _deep_merge(base, raw)
    if t_goal_override is not None:
        merged["T_goal"] = float(t_goal_override)
    validate_pi_ref_config(merged)
    return merged


def _deep_merge(a: Dict[str, Any], b: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v  # type: ignore[assignment]
    return out


def validate_pi_ref_config(cfg: Mapping[str, Any]) -> None:
    hard = cfg["hard"]
    l_min, l_max = float(hard["L_min"]), float(hard["L_max"])
    if l_min < 1 or l_max < l_min:
        raise ValueError("hard.L_min >= 1 y hard.L_max >= L_min")
    ff = cfg["L_ff"]
    for key in ("L_low", "L_mid", "L_high", "E_a", "E_b", "w_a", "w_b"):
        if key not in ff:
            raise ValueError(f"L_ff falta clave {key}")
    if float(ff["w_a"]) <= 0 or float(ff["w_b"]) <= 0:
        raise ValueError("L_ff.w_a y w_b deben ser > 0")
    pi = cfg["pi"]
    for key in ("K_p", "K_i", "I_max"):
        if key not in pi:
            raise ValueError(f"pi falta clave {key}")


def vault_leverage_for_pi(cfg: Mapping[str, Any]) -> float:
    """Leverage para ramas de vault/derisk cuando policy=pi_ref (sustituto de lev_stages[2])."""
    if "vault_leverage" in cfg and cfg["vault_leverage"] is not None:
        return float(cfg["vault_leverage"])
    return float(cfg["hard"]["L_max"])
