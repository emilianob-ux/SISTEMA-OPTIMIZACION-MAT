from __future__ import annotations

import unittest
from pathlib import Path

from dre.measurement import run_mat_measurement_command


class TestDREMeasurement(unittest.TestCase):
    def test_mat_runner_bridge(self) -> None:
        root = Path(__file__).resolve().parents[1]
        db = root / "data" / "synthetic_signal_tune.db"
        if not db.exists():
            self.skipTest("DB sintética no disponible en este entorno")
        payload = run_mat_measurement_command(
            db_path=str(db),
            holdout_frac=0.0,
            repo_root=root,
        )
        self.assertIn("p_win_terminal", payload)
        self.assertIn("p_ruin", payload)
