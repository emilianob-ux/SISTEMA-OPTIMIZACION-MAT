from __future__ import annotations

from typing import Dict, Optional

from dre.contracts.orchestrator_context import ExecutionContext
from dre.storage.base import ContextStore


class MemoryContextStore(ContextStore):
    """Cache volátil en proceso (sustituto MVP de Redis)."""

    def __init__(self) -> None:
        self._ctx: Dict[str, ExecutionContext] = {}

    def get(self, run_id: str) -> Optional[ExecutionContext]:
        return self._ctx.get(run_id)

    def save(self, ctx: ExecutionContext, *, ttl_seconds: int | None = None) -> None:
        _ = ttl_seconds
        self._ctx[ctx.run_id] = ctx

    def delete(self, run_id: str) -> None:
        self._ctx.pop(run_id, None)
