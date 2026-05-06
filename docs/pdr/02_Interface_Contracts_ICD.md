# 02 — Interface Contracts (ICD)

Contratos de interfaz entre componentes del Decision Resilience Engine. Referencia de implementación orientativa (Pydantic v2).

**Implementación ejecutable (subset):** [`dre/contracts/`](../../dre/contracts/) — mantener sincronizado con los snippets de este archivo.

## 2.1 Handoff crítico: Optimizer → StressTest → Backprop

```python
# contracts/stress_feedback.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Dict, Optional

class StressFeedbackPayload(BaseModel):
    failed_constraints: List[str]
    stress_scenarios_failed: List[str]
    slack_violation_magnitude: Dict[str, str]
    recommended_action: Literal[
        "switch_to_stochastic",
        "add_robustness_buffer",
        "relax_soft_with_penalty"
    ]
    action_priority: List[str]
    max_reformulation_iterations: int = 2
    robustness_backpropagation_triggered: bool = True

    @field_validator("recommended_action")
    def must_match_priority(cls, v, info):
        values = info.data
        if "action_priority" in values and v not in values["action_priority"]:
            raise ValueError("recommended_action debe estar en action_priority")
        return v
```

## 2.2 Contrato de estado del orquestador (Redis / GovernanceCore)

```python
# contracts/orchestrator_context.py
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Optional
from datetime import datetime

class ExecutionContext(BaseModel):
    run_id: str = Field(..., pattern=r"^opt_\d{8}_\d{6}_v5\.0$")
    execution_mode: Literal["FAST", "STANDARD", "DEEP_AUDIT"]
    current_state: Literal[
        "IDLE", "ROUTING", "VALIDATING", "FORECASTING", "CAUSAL",
        "OPTIMIZING", "STRESS_TESTING", "BACKPROP", "GOVERNING",
        "OVERRIDE", "MONITORING", "COMPLETED", "FAILED", "ESCALATED"
    ]
    iteration_count: int = Field(ge=0, le=2)
    override_active: bool = False
    stress_scenarios_ref: Optional[str] = None
    checkpoint_refs: List[str] = []
    skill_statuses: Dict[str, str] = {}
    accumulated_warnings: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
```

> **Nota:** En Pydantic v2, preferir `model_serializer` / `SerializationContext` en lugar de `json_encoders` deprecados cuando se implemente en código productivo.

## 2.3 Manejo de errores tipado

```json
{
  "error": "RUN_ID_COLLISION",
  "detail": "Same run_id with different data_hash detected",
  "run_id": "opt_20250418_143022_v5.0",
  "data_hash_expected": "sha256:a1b2...",
  "data_hash_received": "sha256:c3d4...",
  "recovery": "Generate new run_id or verify input pipeline consistency"
}
```
