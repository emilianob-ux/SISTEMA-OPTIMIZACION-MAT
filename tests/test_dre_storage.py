from __future__ import annotations

import unittest

import fakeredis

from dre.contracts.orchestrator_context import ExecutionContext
from dre.storage import RedisContextStore


class TestDREStorage(unittest.TestCase):
    def test_redis_context_store_roundtrip(self) -> None:
        r = fakeredis.FakeRedis()
        store = RedisContextStore(r, key_prefix="t:")
        ctx = ExecutionContext(
            run_id="opt_20260505_190000_v5.0",
            execution_mode="STANDARD",
            current_state="ROUTING",
            iteration_count=0,
        )
        store.save(ctx, ttl_seconds=60)
        loaded = store.get(ctx.run_id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.current_state, "ROUTING")
