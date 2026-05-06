from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from dre.api.app import create_app


class TestDREApi(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "api.sqlite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_health_and_simulate(self) -> None:
        app = create_app(governance_db_path=self.db_path)
        with TestClient(app) as client:
            self.assertEqual(client.get("/dre/health").status_code, 200)

            payload = {
                "run_id": "opt_20260505_140000_v5.0",
                "data_hash": "sha256:1111",
                "rng_seed": 11,
                "variant": "standard",
            }
            res = client.post("/dre/simulate", json=payload)
            self.assertEqual(res.status_code, 200, res.text)
            body = res.json()
            self.assertEqual(body["current_state"], "MONITORING")

    def test_collision_409(self) -> None:
        app = create_app(governance_db_path=self.db_path)
        with TestClient(app) as client:
            base = {
                "run_id": "opt_20260505_150000_v5.0",
                "data_hash": "sha256:aaa",
                "rng_seed": 1,
                "variant": "standard",
            }
            self.assertEqual(client.post("/dre/simulate", json=base).status_code, 200)
            clash = {**base, "data_hash": "sha256:bbb"}
            res = client.post("/dre/simulate", json=clash)
            self.assertEqual(res.status_code, 409)
