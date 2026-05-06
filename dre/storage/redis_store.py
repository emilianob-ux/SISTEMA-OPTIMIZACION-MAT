from __future__ import annotations

from typing import Optional

from dre.contracts.orchestrator_context import ExecutionContext
from dre.storage.base import ContextStore


class RedisContextStore(ContextStore):
    """Store Redis opcional (real o fakeredis), usando JSON del modelo."""

    def __init__(self, redis_client, *, key_prefix: str = "dre:ctx:") -> None:
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _k(self, run_id: str) -> str:
        return f"{self.key_prefix}{run_id}"

    def get(self, run_id: str) -> Optional[ExecutionContext]:
        raw = self.redis.get(self._k(run_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return ExecutionContext.model_validate_json(raw)

    def save(self, ctx: ExecutionContext, *, ttl_seconds: int | None = None) -> None:
        payload = ctx.model_dump_json()
        key = self._k(ctx.run_id)
        if ttl_seconds and ttl_seconds > 0:
            self.redis.setex(key, ttl_seconds, payload)
        else:
            self.redis.set(key, payload)

    def delete(self, run_id: str) -> None:
        self.redis.delete(self._k(run_id))
