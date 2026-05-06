from __future__ import annotations

from typing import Dict, Tuple

from dre.orchestrator.errors import FSMError

_Transitions = Dict[Tuple[str, str], str]

_TRANSITIONS: _Transitions = {
    ("IDLE", "REQUEST_RECEIVED"): "ROUTING",
    ("ROUTING", "CLASSIFIED"): "VALIDATING",
    ("ROUTING", "ROUTING_FAILED"): "FAILED",
    ("VALIDATING", "VALIDATION_PASS"): "FORECASTING",
    ("VALIDATING", "VALIDATION_BLOCKED"): "FAILED",
    ("FORECASTING", "FORECAST_SKIP_CAUSAL"): "OPTIMIZING",
    ("FORECASTING", "FORECAST_NEED_CAUSAL"): "CAUSAL",
    ("CAUSAL", "CAUSAL_PASS"): "OPTIMIZING",
    ("CAUSAL", "CAUSAL_BLOCKED"): "ESCALATED",
    ("OPTIMIZING", "OPTIMIZATION_READY"): "GOVERNING_PARTIAL",
    ("GOVERNING_PARTIAL", "PARTIAL_GOVERNANCE_DONE"): "STRESS_TESTING",
    ("STRESS_TESTING", "STRESS_PASS"): "GOVERNING_FINAL",
    ("STRESS_TESTING", "STRESS_BACKPROP"): "BACKPROP",
    ("STRESS_TESTING", "STRESS_ESCALATE"): "ESCALATED",
    ("BACKPROP", "REFORM_SUCCESS"): "OPTIMIZING",
    ("BACKPROP", "REFORM_INFEASIBLE"): "ESCALATED",
    ("GOVERNING_FINAL", "FINAL_GOVERNANCE_DONE"): "COMPLETED",
    ("COMPLETED", "DEPLOY_MONITOR"): "MONITORING",
    ("MONITORING", "MONITORING_DRIFT"): "ROUTING",
    ("ESCALATED", "OVERRIDE_TO_STRESS"): "STRESS_TESTING",
    ("ESCALATED", "OVERRIDE_REJECT"): "FAILED",
}


def resolve_transition(state: str, event: str) -> str:
    """Devuelve el siguiente estado o lanza `FSMError`."""
    key = (state, event)
    if key not in _TRANSITIONS:
        raise FSMError(f"Transición no definida: state={state!r} event={event!r}")
    return _TRANSITIONS[key]
