from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field, model_validator

RecommendedAction = Literal[
    "switch_to_stochastic",
    "add_robustness_buffer",
    "relax_soft_with_penalty",
]


class StressFeedbackPayload(BaseModel):
    """Handoff Optimizer → StressTest → Backprop (ICD §2.1)."""

    failed_constraints: List[str]
    stress_scenarios_failed: List[str]
    slack_violation_magnitude: Dict[str, str]
    recommended_action: RecommendedAction
    action_priority: List[str]
    max_reformulation_iterations: int = Field(default=2, ge=0, le=2)
    robustness_backpropagation_triggered: bool = True

    @model_validator(mode="after")
    def recommended_in_priority(self) -> StressFeedbackPayload:
        if self.recommended_action not in self.action_priority:
            raise ValueError("recommended_action must appear in action_priority")
        return self
