# Decision Resilience Engine — código (`dre/`)

Implementación **MVP** del DRE alineada con [`docs/pdr/`](../docs/pdr/README.md) y [`docs/DRE_TECHNICAL_ARCHITECTURE.md`](../docs/DRE_TECHNICAL_ARCHITECTURE.md). Estado detallado: [`docs/DRE_IMPLEMENTATION_STATUS.md`](../docs/DRE_IMPLEMENTATION_STATUS.md).

## Estructura

| Ruta | Rol |
|------|-----|
| `contracts/` | Modelos Pydantic ICD (`StressFeedbackPayload`, `ExecutionContext`). |
| `orchestrator/` | FSM (`fsm.py`), pipeline (`engine.py`). |
| `governance/` | Ledger SQLite append-only + colisión `run_id`/`data_hash`. |
| `storage/` | Cache en memoria (sustituto de Redis). |
| `skills/` | Forecasting, stress LP, relajación LP timeboxed, drift, causal tier‑1, override. |
| `api/` | FastAPI: `POST /dre/simulate`, `GET /dre/health`. |
| `core/` | Utilidades (`sha256_text`). |

## Ejecutar API

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/run_dre_api.py --db data/dre_governance.sqlite
```

## Tests

```bash
pytest tests/test_dre_*.py -q
```

## PyPI

El paquete publicado `sistema-optimizacion-mat` **no incluye** `dre/` en la wheel (sigue siendo solo MAT). El DRE se usa desde **clon del repo** o futuro paquete separado.
