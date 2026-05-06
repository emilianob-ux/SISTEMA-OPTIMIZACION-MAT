# Estado de implementación — Decision Resilience Engine (en este repo)

Este documento enlaza la **especificación** (`docs/pdr/`, `docs/DRE_TECHNICAL_ARCHITECTURE.md`) con el **código Python** bajo `dre/`.

## Implementado (MVP ejecutable)

| Componente | Ubicación | Notas |
|------------|-----------|-------|
| Contratos ICD | `dre/contracts/` | `StressFeedbackPayload`, `ExecutionContext` (estados ampliados FSM). |
| FSM | `dre/orchestrator/fsm.py` | Tabla de transiciones alineada al diagrama §5.2 (subset operativo). |
| Orquestación secuencial | `dre/orchestrator/engine.py` | `DrePipeline.simulate_standard_success`, `simulate_intervention_success`. |
| Governance SQLite | `dre/governance/sqlite_store.py` | Registro por `run_id`, idempotencia `(run_id, data_hash)`, bitácora append-only. |
| Cache volátil | `dre/storage/memory.py` | Sustituto de Redis en proceso. |
| Coherencia datos | `dre/skills/coherence.py` | Validación formato `data_hash` y modo. |
| Forecasting lite | `dre/skills/forecasting.py` | Serie univariada + KS vs normal empírica (`scipy`). |
| Stress LP | `dre/skills/stress.py` | Escenarios ΔRHS + `linprog` HiGHS; métricas `infeasibility_rate`, `min_slack_global`. |
| Backprop / relajación LP | `dre/skills/backprop.py` | `linprog` timeboxed (hilo + timeout); reformulaciones simbólicas `cvxpy` pendientes. |
| Drift | `dre/skills/drift.py` | PSI histograma + norma Frobenius entre matrices. |
| Causal Tier-1 | `dre/skills/causal.py` | Overlap histograma + gate umbral 0.6. |
| Override sandbox | `dre/skills/override.py` | Clasificación ΔKPI §6.2. |
| API HTTP | `dre/api/app.py` | `POST /dre/simulate`, `GET /dre/health`. |

## Pendiente / siguiente oleada

| Tema | Prioridad |
|------|-----------|
| Redis real + TTL 72h (`fakeredis` ya usable para tests) | Alta |
| Persistencia FSM completa + checkpoints resume `ESCALATED` | Alta |
| Copulas / KDE FFT / two-stage SP como en §1–§2 doc técnico | Media |
| DoWhy / CausalML nivel 3 | Media |
| Integración explícita **measurement.command → MAT runner** | Media |
| Hooks EU AI Act / retención logs firmada | Legal + ingeniería |

## Pruebas

- Unitarias e integración liviana: `tests/test_dre_*.py`.
- CI instala `requirements-dev.txt` (incluye `scipy`, `fastapi`, `uvicorn`, `httpx`).
