# Sistema de optimización MAT — backtest compuesto (BTC/ETH)

**English:** [README.en.md](README.en.md)

Motor de **simulación por ventanas deslizantes** sobre futuros USDT (precio + funding) con gestión de apalancamiento por equity, reglas de señal opcionales en JSON y barridos reproducibles. Pensado para **investigación cuantitativa**, no como señal de trading en vivo.

[![CI](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml/badge.svg)](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Aviso legal:** esto es software experimental. Los resultados históricos no garantizan rendimiento futuro. Usalo bajo tu propio criterio y cumplimiento normativo.

---

## Por qué este repo puede funcionar bien en GitHub

- **Reproducibilidad:** CI genera una DB mínima y valida tests + una corrida del runner.
- **Contrato explícito:** métricas (`p_win_terminal`, `p_ruin`, walk-forward) y docs del dataset en [`docs/DATASET.md`](docs/DATASET.md).
- **Extensible:** reglas de filtro en JSON (`--signal-config`), spec tipo ce-optimize en YAML de ejemplo.
- **Honestidad metodológica:** tabúes y holdout documentados en `docs/brainstorms/` (evitar curve-fitting descuidado).
- **Índice de docs:** [`docs/README.md`](docs/README.md) (tutorial, dataset, PyPI, ejemplos).

Lo que **no** promete: edge rentable listo para copiar. Open source exitoso aquí = herramienta clara + datos armables + CI verde.

---

## Requisitos

- Python **3.11+** (probado en CI con 3.11 y 3.12).
- Dependencias: `pip install -r requirements.txt`  
  Desarrollo / tests: `pip install -r requirements-dev.txt`

---

## Inicio rápido (sin datos propios)

Tutorial paso a paso (venv, DB sintética, tests, JSON): [`docs/tutorial_quickstart.md`](docs/tutorial_quickstart.md).

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/bootstrap_synthetic_candles_db.py
pytest tests/ -q
python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0.2
```

La salida es **JSON** en stdout (métricas agregadas + opcional `walk_forward`).

Optimización acotada de reglas de señal:

```bash
python scripts/optimize_signal_grid.py --db data/synthetic_signal_tune.db --preset smoke --skip-pairs --holdout-frac 0.2
```

Ver [`docs/signal_rules_examples.md`](docs/signal_rules_examples.md).

---

## Datos reales (Binance Vision)

El repo incluye utilidades bajo `data/binance_vision/` y `scripts/download_binance_vision.py` para armar tu propio `candles.db`. El esquema esperado está en [`docs/DATASET.md`](docs/DATASET.md).

Variable opcional: `COMPOUND_OPT_DB=/ruta/a/candles.db`

---

## Componentes principales

| Pieza | Rol |
|-------|-----|
| [`compound_optimize_runner.py`](compound_optimize_runner.py) | Carga SQLite, cóctel EMA/SMA + anti-whipsaw, equity target/ruina, JSON |
| [`leverage_pi.py`](leverage_pi.py) | Política opcional `pi_ref` (PI + referencia suave) |
| [`features/`](features/) | Indicadores 5m, reglas `--signal-config` |
| [`scripts/optimize_signal_grid.py`](scripts/optimize_signal_grid.py) | Rejilla de señales + gates `p_ruin` / Δ OOS |
| [`optimization/contract.yaml`](optimization/contract.yaml) | Contrato numérico de referencia |

---

## Qué va fuera de este repo público

Estas categorías **no son el núcleo de optimización/backtest** y están en `.gitignore` para mantenerlas solo localmente (u otro repo privado):

- PDFs (`*.pdf`): pitch decks y briefs.
- **`SK-MATHS/`**: documentación conceptual (no el simulador).
- **`multi_agent_trading/`**: otro proyecto.
- Scripts Telegram (`scripts/telegram_hola_bot.py`, `scripts/telegram_scheduler_hola.py`).
- Raíz: generadores `generate_*pdf*.py`, `generate_audience_pdfs.py`, `generate_pitch_pdfs.py`, `generate_pdr_committee_*.py`.
- Raíz: narrativa `PDR_*.md`, `PDR_programa_compras.md`, `DRE_*.md`.
- **`optimization/`**: salidas de corridas (`sweep*.json/jsonl`, `signal_grid*.json`, tablas `signal_grid*.md`, `last_run.json`). Siguen versionados `contract.yaml`, `contract.json`, `mc_ladder.py`, `verify_run.json`.

Para material comercial usá otro repositorio o Releases sin mezclarlo con el código reproducible.

---

## Impulsar alcance en GitHub (lo que más suma)

**Ya versionado en el repo**

- Dependabot (`.github/dependabot.yml`) para PRs de actualización de `numpy`/`requests` y de Actions.
- `pyproject.toml`: metadatos, keywords y `pip install -e ".[dev]"` como alternativa a los `requirements*.txt`.
- [`CHANGELOG.md`](CHANGELOG.md) y ejemplo de JSON del runner en [`docs/examples/`](docs/examples/).

**En la configuración del repo (no son archivos)**

- **Topics** sugeridos: `quantitative-finance`, `backtesting`, `binance`, `cryptocurrency`, `numpy`, `python`, `research`, `futures`.
- **About**: una línea que diga “sliding-window futures backtest (BTC/ETH) + optional signal optimizer”; link a docs/DATASET.
- **Discussions** habilitadas en GitHub para Q&A sin ruido en Issues.
- URLs del proyecto ya apuntan a [`emilianob-ux/SISTEMA-OPTIMIZACION-MAT`](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT) en README y `pyproject.toml`.
- **Stars externos**: post corto en X/LinkedIn/Medium con el quickstart + “no es asesoramiento financiero”.

**Calidad incremental**

- `pre-commit` + `ruff` (lint rápido) cuando el equipo crezca.
- README en inglés: [`README.en.md`](README.en.md) (enlace arriba).
- Publicación opcional en PyPI: [`docs/PUBLISHING_PYPI.md`](docs/PUBLISHING_PYPI.md).

---

## Licencia, seguridad y comunidad

- Licencia: [LICENSE](LICENSE) (MIT).
- Contribuciones: [CONTRIBUTING.md](CONTRIBUTING.md).
- Vulnerabilidades: [SECURITY.md](SECURITY.md) (reporte privado).
- Código de conducta: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

### Checklist antes de publicar el repo

1. Badge CI y `project.urls` ya usan `emilianob-ux/SISTEMA-OPTIMIZACION-MAT`.
2. Confirmar que **no** subís `candles.db` gigante ni API keys (`.gitignore` ya ignora `data/*.db`).
3. Revisar `git status`: no deben subirse PDFs, SK-MATHS, Telegram, PDR/DRE en raíz ni artefactos `optimization/sweep*` / `optimization/signal_grid*` (ver sección anterior).
