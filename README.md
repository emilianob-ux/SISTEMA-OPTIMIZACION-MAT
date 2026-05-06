# Sistema de optimización MAT — backtest compuesto (BTC/ETH)

Motor de **simulación por ventanas deslizantes** sobre futuros USDT (precio + funding), apalancamiento ligado al equity, reglas de señal opcionales en JSON y barridos reproducibles. Pensado para **investigación cuantitativa**, no como señal de trading en vivo.

[![CI](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml/badge.svg)](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/sistema-optimizacion-mat.svg)](https://pypi.org/project/sistema-optimizacion-mat/)

> **Aviso legal:** software experimental. El rendimiento pasado no garantiza resultados futuros. Usalo bajo tu criterio y cumplimiento normativo.

---

## Instalación

**PyPI:**

```bash
pip install sistema-optimizacion-mat
```

**Repo completo** (tests, scripts, DB sintética): cloná el proyecto y seguí [`docs/tutorial_quickstart.md`](docs/tutorial_quickstart.md). También podés usar `pip install -e ".[dev]"` desde la raíz.

---

## Requisitos

- Python **3.11+** (CI usa 3.11 y 3.12).
- `pip install -r requirements.txt` · desarrollo: `pip install -r requirements-dev.txt`

---

## Inicio rápido

Tutorial paso a paso: [`docs/tutorial_quickstart.md`](docs/tutorial_quickstart.md).

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/bootstrap_synthetic_candles_db.py
pytest tests/ -q
python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0.2
```

Salida: **JSON** en stdout (métricas agregadas y opcional `walk_forward`).

Optimización acotada de reglas de señal:

```bash
python scripts/optimize_signal_grid.py --db data/synthetic_signal_tune.db --preset smoke --skip-pairs --holdout-frac 0.2
```

Ejemplos de `--signal-config`: [`docs/signal_rules_examples.md`](docs/signal_rules_examples.md).

---

## Datos reales (Binance Vision)

Utilidades en `data/binance_vision/` y [`scripts/download_binance_vision.py`](scripts/download_binance_vision.py). Esquema SQLite: [`docs/DATASET.md`](docs/DATASET.md).

Variable opcional: `COMPOUND_OPT_DB=/ruta/a/candles.db`

---

## Componentes principales

| Pieza | Rol |
|-------|-----|
| [`compound_optimize_runner.py`](compound_optimize_runner.py) | SQLite, EMA/SMA + anti-whipsaw, equity target/ruina, JSON |
| [`leverage_pi.py`](leverage_pi.py) | Política opcional `pi_ref` (PI + referencia suave) |
| [`features/`](features/) | Indicadores, reglas `--signal-config` |
| [`scripts/optimize_signal_grid.py`](scripts/optimize_signal_grid.py) | Rejilla de señales + gates `p_ruin` / Δ OOS |
| [`optimization/contract.yaml`](optimization/contract.yaml) | Contrato numérico de referencia |
| [`ce-optimize-spec.yaml`](ce-optimize-spec.yaml) | Spec tipo ce-optimize de ejemplo (YAML) |

---

## Decision Resilience Engine (DRE)

Especificación de producto **Decision Resilience Engine** (PDR, ICD, riesgos, V&V, arquitectura técnica v1.1 con diagramas Mermaid):

- Índice del paquete PDR: [`docs/pdr/README.md`](docs/pdr/README.md)
- Arquitectura y metodologías: [`docs/DRE_TECHNICAL_ARCHITECTURE.md`](docs/DRE_TECHNICAL_ARCHITECTURE.md)
- Estado código vs especificación: [`docs/DRE_IMPLEMENTATION_STATUS.md`](docs/DRE_IMPLEMENTATION_STATUS.md)
- Contratos + motor MVP: [`dre/`](dre/README.md)

El runner MAT es el **simulador de dominio**; el DRE incluye aquí **FSM, governance SQLite, skills numéricos y API FastAPI** (MVP). Redis distribuido, copulas completas y niveles causales avanzados están en roadmap en el doc de estado.

**API local (dev):** `pip install -r requirements-dev.txt` y `python scripts/run_dre_api.py --db data/dre_governance.sqlite`  
Endpoints MVP: `POST /dre/simulate`, `POST /dre/resume`, `GET /dre/health`.

---

## Fuera del núcleo público

En `.gitignore`: bases grandes (`data/*.db`), PDFs, `SK-MATHS/`, `multi_agent_trading/`, bots Telegram, generadores `generate_*` en raíz, narrativa comercial suelta en raíz (`PDR_*.md`, etc.), artefactos `optimization/sweep*` / `signal_grid*`. Siguen versionados `contract.yaml`, `contract.json`, `mc_ladder.py`, `verify_run.json` y la documentación técnica bajo `docs/` (incluye `docs/pdr/`).

---

## Licencia y seguridad

- Licencia: [LICENSE](LICENSE) (MIT).
- Reportes de seguridad: [SECURITY.md](SECURITY.md).

Historia de versiones: [CHANGELOG.md](CHANGELOG.md).
