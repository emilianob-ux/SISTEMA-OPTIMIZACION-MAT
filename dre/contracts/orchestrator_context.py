from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ExecutionMode = Literal["FAST", "STANDARD", "DEEP_AUDIT"]

OrchestratorState = Literal[
    "IDLE",
    "ROUTING",
    "VALIDATING",
    "FORECASTING",
    "CAUSAL",
    "OPTIMIZING",
    "STRESS_TESTING",
    "BACKPROP",
    # Escrituras parcial/final de gobernanza (diagrama FSM técnico §5.2)
    "GOVERNING_PARTIAL",
    "GOVERNING_FINAL",
    "GOVERNING",
    "OVERRIDE",
    "MONITORING",
    "COMPLETED",
    "FAILED",
    "ESCALATED",
]


class ExecutionContext(BaseModel):
    """Volatile orchestrator context (ICD §2.2; persistent cache target = Redis)."""

    run_id: str = Field(..., pattern=r"^opt_\d{8}_\d{6}_v5\.0$")
    execution_mode: ExecutionMode
    current_state: OrchestratorState
    iteration_count: int = Field(ge=0, le=2)
    override_active: bool = False
    stress_scenarios_ref: Optional[str] = None
    checkpoint_refs: List[str] = Field(default_factory=list)
    skill_statuses: Dict[str, Any] = Field(default_factory=dict)
    accumulated_warnings: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
