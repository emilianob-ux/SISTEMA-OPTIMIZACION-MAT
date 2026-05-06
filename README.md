# Decision Resilience Engine (DRE) — decision-resilience-engine

**English version:** [README.en.md](README.en.md)

Framework de investigacion y ejecucion centrado en **resiliencia y gobernanza de decisiones** (DRE), con **MAT** como puente de medicion cuantitativa secundario (futuros BTC/ETH):

- **DRE (MVP)**: orquestador con FSM, governance append-only, checkpoints/resume, API FastAPI, storage memoria/Redis y contratos ICD.
- **MAT**: backtest compuesto BTC/ETH (futuros USDT) con ventanas deslizantes, funding y optimizacion de reglas de senal.

[![CI](https://github.com/emilianob-ux/decision-resilience-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/emilianob-ux/decision-resilience-engine/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI — pendiente](https://img.shields.io/badge/PyPI-primer%20release%20pendiente-lightgrey)](docs/PUBLISHING_PYPI.md)

> **Aviso legal:** software experimental para investigacion. El rendimiento pasado no garantiza resultados futuros.

---

## Que aporta este proyecto

- **Resiliencia de decisiones:** flujo con estados, auditoria, colision `run_id`/`data_hash`, checkpoints y reanudacion (DRE).
- **Reproducibilidad:** CI y tests activos, dataset sintetico y contratos versionados.
- **Operabilidad real:** API HTTP, almacenamiento Redis opcional y trazas append-only en SQLite.
- **Extensibilidad:** separacion clara entre skills DRE, contratos ICD y simulador MAT como medicion.

## Demo en 60 segundos

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/bootstrap_synthetic_candles_db.py
python scripts/run_dre_api.py --db data/dre_governance.sqlite
```

En otra terminal:

```bash
curl -X POST "http://127.0.0.1:8000/dre/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "opt_20260506_000100_v5.0",
    "data_hash": "sha256:demo",
    "rng_seed": 7,
    "variant": "standard"
  }'
```

Luego:

```bash
curl -X POST "http://127.0.0.1:8000/dre/resume" \
  -H "Content-Type: application/json" \
  -d '{"run_id":"opt_20260506_000100_v5.0"}'
```

---

## Instalación

### PyPI (cuando exista la primera publicación)

El nombre del proyecto en PyPI será `decision-resilience-engine`, pero **todavía no hay ninguna versión subida** (por eso el indicador gris enlaza a [`docs/PUBLISHING_PYPI.md`](docs/PUBLISHING_PYPI.md)). Cuando publiques la primera wheel, podrás usar:

```bash
pip install decision-resilience-engine
```

La wheel incluirá los módulos **MAT** definidos en `pyproject.toml`; el código **`dre/`** sigue pensado para usarse desde **clon del repositorio**.

### Mientras tanto (instalar desde GitHub)

```bash
pip install "git+https://github.com/emilianob-ux/decision-resilience-engine.git"
```

### Entorno completo del repo (DRE + MAT)

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

---

## Inicio rapido MAT

```bash
python scripts/bootstrap_synthetic_candles_db.py
pytest tests/ -q
python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0.2
```

Salida: JSON en stdout (por ejemplo `p_win_terminal`, `p_ruin`, `walk_forward`).

Optimización de señales:

```bash
python scripts/optimize_signal_grid.py --db data/synthetic_signal_tune.db --preset smoke --skip-pairs --holdout-frac 0.2
```

- Dataset esperado: [`docs/DATASET.md`](docs/DATASET.md)
- Ejemplos `--signal-config`: [`docs/signal_rules_examples.md`](docs/signal_rules_examples.md)

---

## API DRE (MVP)

Levantar servicio:

```bash
python scripts/run_dre_api.py --db data/dre_governance.sqlite
```

Endpoints:

- `GET /dre/health`
- `POST /dre/simulate`
- `POST /dre/resume`

Ejemplo mínimo:

```bash
curl -X POST "http://127.0.0.1:8000/dre/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "opt_20260506_000100_v5.0",
    "data_hash": "sha256:demo",
    "rng_seed": 7,
    "variant": "standard"
  }'
```

---

## Arquitectura y documentos

- Índice docs: [`docs/README.md`](docs/README.md)
- PDR DRE (01–05): [`docs/pdr/README.md`](docs/pdr/README.md)
- Arquitectura técnica DRE v1.1: [`docs/DRE_TECHNICAL_ARCHITECTURE.md`](docs/DRE_TECHNICAL_ARCHITECTURE.md)
- Estado implementacion vs roadmap: [`docs/DRE_IMPLEMENTATION_STATUS.md`](docs/DRE_IMPLEMENTATION_STATUS.md)
- Módulo DRE: [`dre/README.md`](dre/README.md)

---

## Estado actual

- Tests: `pytest tests/ -q` (incluye `test_dre_*`).
- Calidad: `ruff check .`.
- `main` con pipeline estable y documentacion lista para comite tecnico.

---

## Licencia y seguridad

- Licencia: [MIT](LICENSE)
- Reporte de seguridad: [SECURITY.md](SECURITY.md)
- Historial: [CHANGELOG.md](CHANGELOG.md)
