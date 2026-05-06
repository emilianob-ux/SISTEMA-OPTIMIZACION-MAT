from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dre.governance.errors import RunIdCollisionError
from dre.governance.sqlite_store import SqliteGovernanceStore


class TestDREGovernance(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "gov.sqlite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_write_run_idempotent(self) -> None:
        gov = SqliteGovernanceStore(self.path)
        self.assertEqual(
            gov.write_run("opt_20260505_100000_v5.0", "sha256:aaa", {"k": 1}),
            "inserted",
        )
        self.assertEqual(
            gov.write_run("opt_20260505_100000_v5.0", "sha256:aaa", {"k": 2}),
            "already_existed",
        )
        gov.close()

    def test_run_id_collision(self) -> None:
        gov = SqliteGovernanceStore(self.path)
        gov.write_run("opt_20260505_110000_v5.0", "sha256:aaa", {})
        with self.assertRaises(RunIdCollisionError):
            gov.write_run("opt_20260505_110000_v5.0", "sha256:bbb", {})
        gov.close()

    def test_audit_append_only(self) -> None:
        gov = SqliteGovernanceStore(self.path)
        gov.append_audit(
            "opt_20260505_120000_v5.0", "TEST", state_before="IDLE", state_after="ROUTING"
        )
        self.assertEqual(gov.audit_event_count(), 1)
        gov.close()
