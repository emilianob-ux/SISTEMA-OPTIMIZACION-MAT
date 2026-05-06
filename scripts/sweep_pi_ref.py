"""
Barrido de rejilla sobre --leverage-policy pi_ref (compound_optimize_runner.py).

Rejilla por defecto (spec §6): K_p x K_i; opcional barrido de w_a=w_b.

Salida (mismo estilo que sweep_compound_ladder):
  optimization/sweep_pi_ref_<timestamp>.jsonl
  optimization/sweep_pi_ref_<timestamp>_best.json
  optimization/sweep_pi_ref_<timestamp>_manifest.json

Uso (desde la raiz del repo):
  python scripts/sweep_pi_ref.py
  python scripts/sweep_pi_ref.py --target-equity 500 --holdout-frac 0.2
  python scripts/sweep_pi_ref.py --sweep-w --p-ruin-max 0.52
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "compound_optimize_runner.py"
BASE_CONFIG = REPO_ROOT / "configs" / "pi_ref.example.json"
OUT_DIR = REPO_ROOT / "optimization"
WORK = OUT_DIR / "_pi_sweep_work"


def _load_base() -> Dict[str, Any]:
    if BASE_CONFIG.is_file():
        with BASE_CONFIG.open(encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "pi_ref" in raw and isinstance(raw["pi_ref"], dict):
            raw = raw["pi_ref"]
        return raw
    # Fallback mínimo si falta el ejemplo
    return {
        "S_mode": 250,
        "T_goal": 1000,
        "L_ff": {
            "L_low": 5,
            "L_mid": 8,
            "L_high": 10,
            "E_a": 220,
            "E_b": 280,
            "w_a": 15,
            "w_b": 15,
        },
        "hard": {"L_min": 3, "L_max": 12},
        "pi": {"K_p": 0.25, "K_i": 0.05, "I_max": 2.0, "anti_windup": "conditional_freeze"},
    }


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _run_one(
    pi_cfg: Dict[str, Any],
    holdout_frac: float,
    *,
    target_equity: float,
    start_capital: float,
    kill_equity: float,
    t1: float,
    t2: float,
) -> Dict[str, Any]:
    WORK.mkdir(parents=True, exist_ok=True)
    cfg_path = WORK / f"pi_{uuid.uuid4().hex}.json"
    body = copy.deepcopy(pi_cfg)
    body["T_goal"] = float(target_equity)
    cfg_path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    cmd = [
        sys.executable,
        str(RUNNER),
        "--leverage-policy",
        "pi_ref",
        "--leverage-pi-config",
        str(cfg_path),
        "--target-equity",
        str(target_equity),
        "--start-capital",
        str(start_capital),
        "--kill-equity",
        str(kill_equity),
        "--t1",
        str(t1),
        "--t2",
        str(t2),
        "--lev1",
        "10",
        "--lev2",
        "10",
        "--lev3",
        "10",
        "--derisk",
        "0",
        "--early-airbag",
        "false",
    ]
    if holdout_frac and holdout_frac > 0.0:
        cmd += ["--holdout-frac", str(holdout_frac)]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    kp = body["pi"]["K_p"]
    ki = body["pi"]["K_i"]
    wa = body["L_ff"]["w_a"]
    wb = body["L_ff"]["w_b"]
    row: Dict[str, Any] = {
        "K_p": kp,
        "K_i": ki,
        "w_a": wa,
        "w_b": wb,
        "elapsed_ms": elapsed_ms,
        "exit_code": proc.returncode,
    }
    try:
        cfg_path.unlink(missing_ok=True)
    except OSError:
        pass
    if proc.stderr.strip():
        row["stderr_tail"] = proc.stderr.strip()[-400:]
    raw = proc.stdout.strip()
    try:
        metrics = json.loads(raw)
    except json.JSONDecodeError:
        row["parse_error"] = True
        row["stdout_tail"] = raw[-800:]
        return row
    if isinstance(metrics, dict) and metrics.get("error"):
        row["runner_error"] = metrics
        return row
    row.update(metrics)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p-ruin-max", type=float, default=0.55)
    ap.add_argument("--holdout-frac", type=float, default=0.0)
    ap.add_argument("--target-equity", type=float, default=1000.0)
    ap.add_argument("--start-capital", type=float, default=140.0)
    ap.add_argument("--kill-equity", type=float, default=70.0)
    ap.add_argument(
        "--t1",
        type=float,
        default=280.0,
        help="Solo métricas condicionales / vault trigger (runner).",
    )
    ap.add_argument("--t2", type=float, default=400.0)
    ap.add_argument(
        "--sweep-w",
        action="store_true",
        help=(
            "Añade w_a=w_b en {12,15,18} al producto (27 corridas con grid K_p x K_i por defecto)."
        ),
    )
    ap.add_argument("--out-dir", type=str, default=str(OUT_DIR))
    args = ap.parse_args()

    if not RUNNER.is_file():
        print(f"No existe runner: {RUNNER}", file=sys.stderr)
        raise SystemExit(1)

    base = _load_base()
    k_ps = (0.0, 0.25, 0.5)
    k_is = (0.0, 0.05, 0.1)
    w_opts: Tuple[float, ...]
    if args.sweep_w:
        w_opts = (12.0, 15.0, 18.0)
    else:
        w = float(base["L_ff"]["w_a"])
        w_opts = (w,)

    combos: List[Dict[str, Any]] = []
    for kp, ki, w in product(k_ps, k_is, w_opts):
        cfg = copy.deepcopy(base)
        cfg["pi"] = dict(cfg.get("pi", {}))
        cfg["pi"]["K_p"] = float(kp)
        cfg["pi"]["K_i"] = float(ki)
        cfg["L_ff"] = dict(cfg.get("L_ff", {}))
        cfg["L_ff"]["w_a"] = float(w)
        cfg["L_ff"]["w_b"] = float(w)
        combos.append(cfg)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tag = "pi_ref_w" if args.sweep_w else "pi_ref"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"sweep_{tag}_{ts}.jsonl"
    total = len(combos)

    print(
        f"Sweep={tag} runs={total} gate_p_ruin<={args.p_ruin_max} "
        f"target={args.target_equity} holdout={args.holdout_frac}",
        flush=True,
    )

    manifest = {
        "sweep": tag,
        "p_ruin_max": args.p_ruin_max,
        "holdout_frac": args.holdout_frac,
        "target_equity": args.target_equity,
        "k_p_grid": list(k_ps),
        "k_i_grid": list(k_is),
        "w_sweep": args.sweep_w,
        "total_runs": total,
        "runner": str(RUNNER),
        "base_config": str(BASE_CONFIG) if BASE_CONFIG.is_file() else None,
    }
    try:
        manifest["git_head"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        manifest["git_head"] = None
    db_candidates = [
        REPO_ROOT / "data" / "candles.db",
        (REPO_ROOT.parent / "BOTS TRADING" / "data" / "candles.db").resolve(),
    ]
    for dbp in db_candidates:
        if dbp.is_file():
            h = hashlib.sha256()
            with dbp.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            manifest["db_path"] = str(dbp)
            manifest["db_sha256"] = h.hexdigest()
            break
    manifest_path = out_dir / f"sweep_{tag}_{ts}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    rows: List[Dict[str, Any]] = []
    for i, cfg in enumerate(combos, start=1):
        kp, ki = cfg["pi"]["K_p"], cfg["pi"]["K_i"]
        w_ab = cfg["L_ff"]["w_a"]
        print(f"[{i}/{total}] K_p={kp} K_i={ki} w_a=w_b={w_ab}", flush=True)
        row = _run_one(
            cfg,
            args.holdout_frac,
            target_equity=args.target_equity,
            start_capital=args.start_capital,
            kill_equity=args.kill_equity,
            t1=args.t1,
            t2=args.t2,
        )
        rows.append(row)
        with jsonl_path.open("a", encoding="utf-8") as f:
            slim = {k: v for k, v in row.items() if k != "leverage_pi_config"}
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")

    ok = [
        r
        for r in rows
        if r.get("exit_code") == 0
        and "p_win_terminal" in r
        and r.get("p_ruin", 99) <= args.p_ruin_max + 1e-12
    ]
    ok.sort(key=lambda r: (r["p_win_terminal"], -r["p_ruin"]), reverse=True)
    best = ok[0] if ok else None
    top5 = ok[:5]
    best_path = out_dir / f"sweep_{tag}_{ts}_best.json"
    summary = {
        "sweep": tag,
        "p_ruin_max": args.p_ruin_max,
        "holdout_frac": args.holdout_frac,
        "target_equity": args.target_equity,
        "total_runs": total,
        "feasible_count": len(ok),
        "best_feasible": best,
        "top5_feasible": top5,
        "jsonl": str(jsonl_path),
        "manifest": str(manifest_path),
    }
    best_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
