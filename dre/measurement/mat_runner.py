from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_mat_measurement_command(
    *,
    db_path: str,
    holdout_frac: float = 0.2,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Puente DRE -> motor MAT (measurement.command estilo ce-optimize)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    cmd = [
        sys.executable,
        "compound_optimize_runner.py",
        "--db",
        db_path,
        "--holdout-frac",
        str(holdout_frac),
    ]
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"MAT runner failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"MAT runner JSON inválido: {exc}") from exc
    return payload
