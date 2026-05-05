"""
Ejecuta compound_optimize_runner con varios JSON de --signal-config y resume métricas.

Uso:
  python scripts/signal_feature_sweep.py --db data/candles.db configs/signal/*.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _ROOT / "compound_optimize_runner.py"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("configs", nargs="+", help="Archivos JSON de reglas")
    p.add_argument("--extra", nargs="*", default=[], help="Args extra al runner, ej. --holdout-frac 0.2")
    args = p.parse_args()
    rows = []
    for cfg in args.configs:
        cmd = [
            sys.executable,
            str(_RUNNER),
            "--db",
            args.db,
            "--signal-config",
            str(Path(cfg).resolve()),
            *args.extra,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_ROOT))
        if proc.returncode != 0:
            rows.append({"config": cfg, "error": proc.stderr or proc.stdout})
            continue
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            rows.append({"config": cfg, "error": "invalid_json", "raw": proc.stdout[:500]})
            continue
        rows.append(
            {
                "config": cfg,
                "p_win_terminal": out.get("p_win_terminal"),
                "p_ruin": out.get("p_ruin"),
                "p_survive_medium": out.get("p_survive_medium"),
                "n_paths": out.get("n_paths"),
            }
        )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
