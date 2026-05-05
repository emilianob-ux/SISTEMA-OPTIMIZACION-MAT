"""
Monte Carlo de barrera con escalera de apalancamiento (surrogate).
Objetivo: maximizar P(toque target) con gate P(ruina) <= umbral.

No modela funding Binance ni el coctel real: calibra un proceso lognormal
multiplicativo para que el baseline (apalancamiento constante) se acerque
a las probabilidades del Coctel informadas (~7.9% win, ~50.9% ruin),
luego optimiza la escalera en rejilla.

Reproducibilidad y acoplamiento (post-calibracion):
  Baseline y cada celda de la rejilla usan el mismo seed y n_paths
  (CLI o optimization/contract.json). Tras calibrate_baseline, se
  pre-genera una matriz Z[path_i, t] con random.Random(seed) y todas
  las corridas run_mc de comparacion (baseline + grid) consumen esas
  mismas Z por (trayectoria, paso), de modo que la diferencia de tasas
  entre politicas viene solo del apalancamiento por equity, no de ruido
  independiente por celda (CRN completo a nivel trayectoria-tiempo).
  La calibracion (rejilla mu/sigma) sigue usando run_mc con RNG secuencial
  por celda; no comparte la matriz Z con la fase de comparacion.

Uso:
  python optimization/mc_ladder.py
  python optimization/mc_ladder.py --n-paths 1000 --seed 42 --json-out optimization/last_run.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent
CONTRACT_JSON = ROOT / "contract.json"


@dataclass
class OutcomeCounts:
    win: int
    ruin: int
    survive: int

    def to_rates(self, n: int) -> Dict[str, float]:
        return {
            "p_win": self.win / n,
            "p_ruin": self.ruin / n,
            "p_survive": self.survive / n,
        }


def load_contract() -> dict:
    with CONTRACT_JSON.open(encoding="utf-8") as f:
        return json.load(f)


def precompute_gaussian_shocks(*, n_paths: int, max_steps: int, seed: int) -> List[List[float]]:
    """Matriz Z[i,t] reproducible para acoplar trayectorias entre politicas."""
    rng = random.Random(seed)
    return [[rng.gauss(0.0, 1.0) for _ in range(max_steps)] for _ in range(n_paths)]


def simulate_path(
    rng: Optional[random.Random],
    *,
    max_steps: int,
    e0: float,
    target: float,
    ruin: float,
    mu: float,
    sigma: float,
    leverage_fn: Callable[[float], float],
    z_sequence: Optional[List[float]] = None,
) -> str:
    """Retorna 'win' | 'ruin' | 'survive' (horizonte sin absorcion)."""
    e = e0
    for step in range(max_steps):
        if e >= target:
            return "win"
        if e <= ruin:
            return "ruin"
        lev = leverage_fn(e)
        if z_sequence is not None:
            z = z_sequence[step]
        else:
            assert rng is not None
            z = rng.gauss(0.0, 1.0)
        r = (mu - 0.5 * sigma * sigma) + sigma * z
        r_eff = lev * r
        r_eff = max(min(r_eff, 2.0), -0.95)
        e *= math.exp(r_eff)
    if e >= target:
        return "win"
    if e <= ruin:
        return "ruin"
    return "survive"


def run_mc(
    *,
    n_paths: int,
    seed: int,
    max_steps: int,
    e0: float,
    target: float,
    ruin: float,
    mu: float,
    sigma: float,
    leverage_fn: Callable[[float], float],
    shock_matrix: Optional[List[List[float]]] = None,
) -> OutcomeCounts:
    rng: Optional[random.Random] = None if shock_matrix is not None else random.Random(seed)
    w = ru = sv = 0
    for i in range(n_paths):
        z_seq = shock_matrix[i] if shock_matrix is not None else None
        o = simulate_path(
            rng,
            max_steps=max_steps,
            e0=e0,
            target=target,
            ruin=ruin,
            mu=mu,
            sigma=sigma,
            leverage_fn=leverage_fn,
            z_sequence=z_seq,
        )
        if o == "win":
            w += 1
        elif o == "ruin":
            ru += 1
        else:
            sv += 1
    return OutcomeCounts(win=w, ruin=ru, survive=sv)


def calibrate_baseline(
    *,
    n_paths: int,
    seed: int,
    max_steps: int,
    e0: float,
    target: float,
    ruin: float,
    l0: float,
    target_win: float,
    target_ruin: float,
) -> Tuple[float, float, Dict[str, float]]:
    """Rejilla compacta (mu, sigma) vs targets de win/ruin del baseline."""
    best_err = 1e9
    best_mu = 0.0
    best_sig = 0.004
    best_rates: Dict[str, float] = {}
    rng = random.Random(seed + 911)
    trials = 72
    for _ in range(trials):
        mu = rng.uniform(-0.00035, 0.00015)
        sigma = rng.uniform(0.0011, 0.0045)
        if sigma <= 0:
            continue

        def lev(_: float) -> float:
            return l0

        c = run_mc(
            n_paths=n_paths,
            seed=seed,
            max_steps=max_steps,
            e0=e0,
            target=target,
            ruin=ruin,
            mu=mu,
            sigma=sigma,
            leverage_fn=lev,
        )
        rw = c.win / n_paths
        rr = c.ruin / n_paths
        err = (rw - target_win) ** 2 + (rr - target_ruin) ** 2
        if err < best_err:
            best_err = err
            best_mu, best_sig = mu, sigma
            best_rates = c.to_rates(n_paths)
    return best_mu, best_sig, {"rates": best_rates, "calibration_error": best_err}


def grid_optimize(
    *,
    n_paths: int,
    seed: int,
    max_steps: int,
    e0: float,
    target: float,
    ruin: float,
    mu: float,
    sigma: float,
    thresholds: List[float],
    lows: List[float],
    highs: List[float],
    p_ruin_max: float,
    shock_matrix: Optional[List[List[float]]] = None,
) -> List[Dict]:
    rows = []
    for thr in thresholds:
        for llo in lows:
            for lhi in highs:
                if llo >= lhi:
                    continue

                def lev(e: float, thr=thr, llo=llo, lhi=lhi) -> float:
                    return llo if e < thr else lhi

                c = run_mc(
                    n_paths=n_paths,
                    seed=seed,
                    max_steps=max_steps,
                    e0=e0,
                    target=target,
                    ruin=ruin,
                    mu=mu,
                    sigma=sigma,
                    leverage_fn=lev,
                    shock_matrix=shock_matrix,
                )
                rates = c.to_rates(n_paths)
                feasible = rates["p_ruin"] <= p_ruin_max
                score = rates["p_win"] - 0.25 * rates["p_ruin"]
                rows.append(
                    {
                        "threshold": thr,
                        "leverage_low": llo,
                        "leverage_high": lhi,
                        "p_win": rates["p_win"],
                        "p_ruin": rates["p_ruin"],
                        "p_survive": rates["p_survive"],
                        "feasible_gate": feasible,
                        "score": score,
                    }
                )
    rows.sort(key=lambda r: (r["feasible_gate"], r["p_win"], -r["p_ruin"]), reverse=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-paths", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--json-out", type=str, default=None)
    ap.add_argument("--calibration-target-win", type=float, default=0.079)
    ap.add_argument("--calibration-target-ruin", type=float, default=0.509)
    args = ap.parse_args()
    t0 = time.perf_counter()

    cfg = load_contract()
    eq = cfg["equity"]
    mc = cfg["monte_carlo"]
    sim = cfg["simulation"]
    gates = cfg["gates"]
    lad = cfg["ladder_search"]

    n_paths = args.n_paths or mc["n_paths"]
    seed = args.seed if args.seed is not None else mc["seed"]
    max_steps = sim["max_steps"]
    e0, target, ruin = eq["initial"], eq["target"], eq["ruin"]
    l0 = lad["baseline_leverage"]

    calib_paths = min(n_paths, 6000)
    mu, sigma, calib_meta = calibrate_baseline(
        n_paths=calib_paths,
        seed=seed,
        max_steps=max_steps,
        e0=e0,
        target=target,
        ruin=ruin,
        l0=l0,
        target_win=args.calibration_target_win,
        target_ruin=args.calibration_target_ruin,
    )

    def lev_baseline(_: float) -> float:
        return l0

    shock_matrix = precompute_gaussian_shocks(
        n_paths=n_paths, max_steps=max_steps, seed=seed
    )

    base_counts = run_mc(
        n_paths=n_paths,
        seed=seed,
        max_steps=max_steps,
        e0=e0,
        target=target,
        ruin=ruin,
        mu=mu,
        sigma=sigma,
        leverage_fn=lev_baseline,
        shock_matrix=shock_matrix,
    )
    base_rates = base_counts.to_rates(n_paths)

    rows = grid_optimize(
        n_paths=n_paths,
        seed=seed,
        max_steps=max_steps,
        e0=e0,
        target=target,
        ruin=ruin,
        mu=mu,
        sigma=sigma,
        thresholds=list(lad["thresholds"]),
        lows=list(lad["leverage_low"]),
        highs=list(lad["leverage_high"]),
        p_ruin_max=gates["p_ruin_max"],
        shock_matrix=shock_matrix,
    )
    best_feasible = next((r for r in rows if r["feasible_gate"]), None)

    report = {
        "contract": cfg,
        "calibration": {
            "mu": mu,
            "sigma": sigma,
            "baseline_leverage": l0,
            "target_win": args.calibration_target_win,
            "target_ruin": args.calibration_target_ruin,
            "calibration_error": calib_meta["calibration_error"],
            "calibration_rates_subsample": calib_meta["rates"],
            "note": "Calibracion con min(n_paths,6000) trayectorias; baseline+rejilla usan shock_matrix CRN.",
        },
        "baseline_full_n": {
            "n_paths": n_paths,
            "seed": seed,
            "rates": base_rates,
        },
        "best_feasible_under_p_ruin_gate": best_feasible,
        "top_by_p_win": sorted(rows, key=lambda r: r["p_win"], reverse=True)[:12],
        "disclaimer": (
            "Surrogate lognormal con barreras; no sustituye hydra.backtest con funding real. "
            "Metodo: rejilla + MC + gate p_ruin. "
            "Post-calibracion, baseline y ladder comparten la misma matriz Z por (trayectoria, paso) "
            "y el mismo seed/n_paths del contrato; la calibracion mu/sigma no usa esa matriz."
        ),
        "wall_time_ms": int((time.perf_counter() - t0) * 1000),
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.json_out:
        outp = Path(args.json_out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
