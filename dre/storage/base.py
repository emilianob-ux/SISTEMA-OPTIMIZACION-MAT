from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from dre.contracts.orchestrator_context import ExecutionContext


class ContextStore(ABC):
    @abstractmethod
    def get(self, run_id: str) -> Optional[ExecutionContext]:
        raise NotImplementedError

    @abstractmethod
    def save(self, ctx: ExecutionContext, *, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, run_id: str) -> None:
        raise NotImplementedError
