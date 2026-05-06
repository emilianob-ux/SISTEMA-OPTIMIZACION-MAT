from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dre.governance.sqlite_store import SqliteGovernanceStore
from dre.orchestrator.engine import DrePipeline


class TestDREPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.gov_path = Path(self.tmp.name) / "gov.sqlite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_standard_success_completes(self) -> None:
        gov = SqliteGovernanceStore(self.gov_path)
        pipe = DrePipeline(gov)
        ctx = pipe.simulate_standard_success(
            "opt_20260505_130000_v5.0",
            "sha256:deadbeef",
            rng_seed=3,
        )
        self.assertEqual(ctx.current_state, "MONITORING")
        self.assertGreater(gov.audit_event_count(), 5)
        gov.close()

    def test_intervention_path(self) -> None:
        gov = SqliteGovernanceStore(self.gov_path)
        pipe = DrePipeline(gov)
        ctx = pipe.simulate_intervention_success(
            "opt_20260505_131500_v5.0",
            "sha256:cafe",
            rng_seed=9,
        )
        self.assertEqual(ctx.current_state, "MONITORING")
        gov.close()

    def test_resume_latest_checkpoint(self) -> None:
        gov = SqliteGovernanceStore(self.gov_path)
        pipe = DrePipeline(gov)
        done = pipe.simulate_standard_success(
            "opt_20260505_171000_v5.0",
            "sha256:bead",
            rng_seed=5,
        )
        resumed = pipe.resume_latest("opt_20260505_171000_v5.0")
        self.assertEqual(done.current_state, resumed.current_state)
        self.assertEqual(resumed.current_state, "MONITORING")
        gov.close()
