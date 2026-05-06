# Decision Resilience Engine (DRE) — decision-resilience-engine

**Spanish version (canonical):** [README.md](README.md)

Research and execution framework focused on **decision resilience and governance** (DRE), with **MAT** as a secondary quantitative measurement bridge (BTC/ETH futures):

- **DRE (MVP)**: state-machine orchestration, append-only governance, checkpoints/resume, FastAPI endpoints, memory/Redis context stores, and ICD contracts.
- **MAT**: compound backtesting with sliding windows, funding costs, and signal-rule optimization.

[![CI](https://github.com/emilianob-ux/decision-resilience-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/emilianob-ux/decision-resilience-engine/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI legacy](https://img.shields.io/pypi/v/sistema-optimizacion-mat.svg?label=PyPI%20%28legacy%29)](https://pypi.org/project/sistema-optimizacion-mat/)
[![PyPI new name](https://img.shields.io/badge/decision--resilience--engine-on%20PyPI-pending-lightgrey)](docs/PUBLISHING_PYPI.md)

> Experimental software for research. Past performance does not imply future results.

**PyPI:** releases still ship under the legacy name [`sistema-optimizacion-mat`](https://pypi.org/project/sistema-optimizacion-mat/) (`pip install sistema-optimizacion-mat`). The new PyPI project [`decision-resilience-engine`](https://pypi.org/project/decision-resilience-engine/) appears after the first successful upload—follow the ordered checklist in [`docs/PUBLISHING_PYPI.md`](docs/PUBLISHING_PYPI.md). For latest `main`, use `pip install "git+https://github.com/emilianob-ux/decision-resilience-engine.git"`.

## Quick demo

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/bootstrap_synthetic_candles_db.py
python scripts/run_dre_api.py --db data/dre_governance.sqlite
```

Then call:

- `POST /dre/simulate`
- `POST /dre/resume`
- `GET /dre/health`

## Docs

- PyPI publishing (maintainers): [`docs/PUBLISHING_PYPI.md`](docs/PUBLISHING_PYPI.md)
- Docs index: [`docs/README.md`](docs/README.md)
- DRE PDR package: [`docs/pdr/README.md`](docs/pdr/README.md)
- Technical architecture: [`docs/DRE_TECHNICAL_ARCHITECTURE.md`](docs/DRE_TECHNICAL_ARCHITECTURE.md)
- Implementation status: [`docs/DRE_IMPLEMENTATION_STATUS.md`](docs/DRE_IMPLEMENTATION_STATUS.md)

