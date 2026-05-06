# Sistema de optimizacion MAT + Decision Resilience Engine (DRE)

**English version:** [README.en.md](README.en.md)

Framework de investigacion y ejecucion para **optimizacion cuantitativa resiliente**:

- **MAT**: backtest compuesto BTC/ETH (futuros USDT) con ventanas deslizantes, funding y optimizacion de reglas de senal.
- **DRE (MVP)**: orquestador con FSM, governance append-only, checkpoints/resume, API FastAPI, storage memoria/Redis y puente de medicion a MAT.

[![CI](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml/badge.svg)](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/sistema-optimizacion-mat.svg)](https://pypi.org/project/sistema-optimizacion-mat/)

> **Aviso legal:** software experimental para investigacion. El rendimiento pasado no garantiza resultados futuros.

---

## Que aporta este proyecto

- **Reproducibilidad:** CI y tests activos, dataset sintetico y contratos versionados.
- **Resiliencia de decisiones:** flujo con estados, auditoria, colision `run_id`/`data_hash`, checkpoints y reanudacion.
- **Operabilidad real:** API HTTP, almacenamiento Redis opcional y trazas append-only en SQLite.
- **Extensibilidad:** separación clara entre simulador MAT, skills DRE y contratos ICD.

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

### Uso rápido desde PyPI (MAT)

```bash
pip install sistema-optimizacion-mat
```

### Entorno completo del repo (MAT + DRE)

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
