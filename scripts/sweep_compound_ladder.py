"""
Barrido de rejilla sobre compound_optimize_runner.py (JSON en stdout).

Presets:
  quick   — pocas combinaciones (~12 corridas con baseline 10/10/10; ~4–5 min)
  medium  — rejilla moderada (~36 corridas)
  full    — exploracion mas amplia (~96 corridas; puede tardar ~30+ min)
  sprint500 — meta 140->500 (usar --target-equity 500): rejilla acotada ~18 corridas
  sprint500_push — apalancamiento mas alto para buscar ~30% p_win (meta 500); ~48 corridas

Salida:
  optimization/sweep_<preset>_<timestamp>.jsonl  (una linea JSON por corrida)
  optimization/sweep_<preset>_<timestamp>_best.json  (mejor factible + top-5)
  optimization/sweep_<preset>_<timestamp>_manifest.json  (git head, db sha, holdout_frac)

Uso (desde la raiz del repo):
  python scripts/sweep_compound_ladder.py --preset quick
  python scripts/sweep_compound_ladder.py --preset medium --p-ruin-max 0.52
  python scripts/sweep_compound_ladder.py --preset quick --holdout-frac 0.2

Politica PI (--leverage-policy pi_ref): ver scripts/sweep_pi_ref.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "compound_optimize_runner.py"
OUT_DIR = REPO_ROOT / "optimization"


@dataclass(frozen=True)
class Grid:
    lev1: Tuple[float, ...]
    lev2: Tuple[float, ...]
    lev3: Tuple[float, ...]
    t1: Tuple[float, ...]
    t2: Tuple[float, ...]
    derisk: Tuple[float, ...]
    early_airbag: str = "false"


PRESETS: Dict[str, Grid] = {
    "quick": Grid(
        # Incluye baseline 10/10/10 (misma politica en las 3 etapas) para anclar la rejilla.
        lev1=(5.0, 6.0, 10.0),
        lev2=(8.0, 10.0),
        lev3=(10.0,),
        t1=(250.0, 280.0),
        t2=(400.0,),
        derisk=(0.0,),
    ),
    "medium": Grid(
        lev1=(4.0, 5.0, 6.0),
        lev2=(8.0, 10.0),
        lev3=(10.0, 12.0),
        t1=(220.0, 250.0, 280.0),
        t2=(400.0,),
        derisk=(0.0, 0.05),
    ),
    "full": Grid(
        lev1=(3.0, 4.0, 5.0, 6.0),
        lev2=(8.0, 10.0, 12.0),
        lev3=(10.0, 12.0),
        t1=(220.0, 250.0, 280.0, 300.0),
        t2=(380.0, 400.0),
        derisk=(0.0, 0.05, 0.1),
    ),
    # Objetivo mas cercano (500 USD): umbrales bajo la meta;
    # apalancamiento algo mas agresivo al final.
    "sprint500": Grid(
        lev1=(6.0, 8.0, 10.0),
        lev2=(10.0, 12.0),
        lev3=(12.0,),
        t1=(190.0, 220.0, 250.0),
        t2=(320.0, 360.0),
        derisk=(0.0,),
    ),
    "sprint500_push": Grid(
        lev1=(10.0, 12.0),
        lev2=(12.0, 14.0),
        lev3=(14.0, 16.0),
        t1=(180.0, 200.0, 220.0),
        t2=(280.0, 300.0),
        derisk=(0.0,),
    ),
}


def _run_one(
    params: Dict[str, Any],
    holdout_frac: float,
    *,
    target_equity: float,
    start_capital: float,
    kill_equity: float,
) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(RUNNER),
        "--target-equity",
        str(target_equity),
        "--start-capital",
        str(start_capital),
        "--kill-equity",
        str(kill_equity),
        "--lev1",
        str(params["lev1"]),
        "--lev2",
        str(params["lev2"]),
        "--lev3",
        str(params["lev3"]),
        "--t1",
        str(params["t1"]),
        "--t2",
        str(params["t2"]),
        "--derisk",
        str(params["derisk"]),
        "--early-airbag",
        str(params.get("early_airbag", "false")),
    ]
    if holdout_frac and holdout_frac > 0.0:
        cmd += ["--holdout-frac", str(holdout_frac)]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    row: Dict[str, Any] = {**params, "elapsed_ms": elapsed_ms, "exit_code": proc.returncode}
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


def _iter_configs(grid: Grid) -> Iterable[Dict[str, Any]]:
    for lev1, lev2, lev3, t1, t2, derisk in product(
        grid.lev1,
        grid.lev2,
        grid.lev3,
        grid.t1,
        grid.t2,
        grid.derisk,
    ):
        # Permitir lev1==lev2==lev3 (baseline fijo).
        # Descartar escaleras estrictamente crecientes mal ordenadas.
        if lev1 > lev2 + 1e-9 or lev2 > lev3 + 1e-9:
            continue
        yield {
            "lev1": lev1,
            "lev2": lev2,
            "lev3": lev3,
            "t1": t1,
            "t2": t2,
            "derisk": derisk,
            "early_airbag": grid.early_airbag,
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=sorted(PRESETS.keys()), default="quick")
    ap.add_argument("--p-ruin-max", type=float, default=0.55)
    ap.add_argument(
        "--holdout-frac",
        type=float,
        default=0.0,
        help="Si >0, pasa --holdout-frac al runner (R8 walk-forward liviano en JSON).",
    )
    ap.add_argument(
        "--target-equity",
        type=float,
        default=1000.0,
        help="Meta WIN (USD). Para sprint 140->500 usar 500.",
    )
    ap.add_argument("--start-capital", type=float, default=140.0)
    ap.add_argument("--kill-equity", type=float, default=70.0)
    ap.add_argument("--out-dir", type=str, default=str(OUT_DIR))
    args = ap.parse_args()

    if not RUNNER.is_file():
        print(f"No existe runner: {RUNNER}", file=sys.stderr)
        raise SystemExit(1)

    grid = PRESETS[args.preset]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"sweep_{args.preset}_{ts}.jsonl"

    rows: List[Dict[str, Any]] = []
    configs = list(_iter_configs(grid))
    total = len(configs)
    print(
        f"Preset={args.preset} combinaciones={total} gate_p_ruin<={args.p_ruin_max} "
        f"target={args.target_equity} start={args.start_capital} kill={args.kill_equity}",
        flush=True,
    )

    manifest = {
        "preset": args.preset,
        "p_ruin_max": args.p_ruin_max,
        "holdout_frac": args.holdout_frac,
        "target_equity": args.target_equity,
        "start_capital": args.start_capital,
        "kill_equity": args.kill_equity,
        "total_configs": total,
        "python": sys.executable,
        "runner": str(RUNNER),
    }
    try:
        rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        manifest["git_head"] = rev
    except Exception:
        manifest["git_head"] = None

    db_candidates = [
        REPO_ROOT / "data" / "candles.db",
        (REPO_ROOT.parent / "BOTS TRADING" / "data" / "candles.db").resolve(),
    ]
    manifest["default_db_path"] = None
    manifest["default_db_sha256"] = None
    for dbp in db_candidates:
        if dbp.is_file():
            h = hashlib.sha256()
            with dbp.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            manifest["default_db_path"] = str(dbp)
            manifest["default_db_sha256"] = h.hexdigest()
            break

    manifest_path = out_dir / f"sweep_{args.preset}_{ts}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    for i, cfg in enumerate(configs, start=1):
        lev_s = f"{cfg['lev1']}/{cfg['lev2']}/{cfg['lev3']}"
        print(
            f"[{i}/{total}] lev={lev_s} t1={cfg['t1']} t2={cfg['t2']} derisk={cfg['derisk']}",
            flush=True,
        )
        row = _run_one(
            cfg,
            args.holdout_frac,
            target_equity=args.target_equity,
            start_capital=args.start_capital,
            kill_equity=args.kill_equity,
        )
        rows.append(row)
        with jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

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

    best_path = out_dir / f"sweep_{args.preset}_{ts}_best.json"
    summary = {
        "preset": args.preset,
        "p_ruin_max": args.p_ruin_max,
        "holdout_frac": args.holdout_frac,
        "target_equity": args.target_equity,
        "start_capital": args.start_capital,
        "kill_equity": args.kill_equity,
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
