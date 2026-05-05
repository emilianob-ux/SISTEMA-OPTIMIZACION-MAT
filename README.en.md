# MAT optimization system — compound backtest (BTC/ETH)

**English README:** sliding-window simulation engine for USDT-margined futures (price + funding), leverage tied to equity, optional JSON signal rules, reproducible sweeps. Intended for **quantitative research**, not live trading signals.

→ **Spanish (canonical copy):** [README.md](README.md)

[![CI](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml/badge.svg)](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Disclaimer:** experimental software. Past performance does not imply future results. Use at your own risk and in compliance with applicable regulation.

---

## Why this repo works well on GitHub

- **Reproducibility:** CI builds a minimal SQLite dataset and runs tests plus one runner invocation.
- **Explicit contract:** metrics (`p_win_terminal`, `p_ruin`, walk-forward) and dataset docs in [`docs/DATASET.md`](docs/DATASET.md).
- **Extensible:** filter rules in JSON (`--signal-config`), sample ce-optimize-style YAML spec.
- **Methodological honesty:** taboos and holdout documented under `docs/brainstorms/` (avoid careless curve-fitting).
- **Doc index:** [`docs/README.md`](docs/README.md).

What it **does not** promise: a plug-and-play profitable edge. Success here = clear tooling + buildable data + green CI.

---

## Requirements

- Python **3.11+** (CI runs 3.11 and 3.12).
- Core deps: `pip install -r requirements.txt`  
  Dev / tests: `pip install -r requirements-dev.txt`  
  Editable install: `pip install -e ".[dev]"` from repo root.

---

## Quick start (no private data)

Step-by-step: [`docs/tutorial_quickstart.md`](docs/tutorial_quickstart.md) (Spanish).

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/bootstrap_synthetic_candles_db.py
pytest tests/ -q
python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0.2
```

Output is **JSON** on stdout (aggregate metrics plus optional `walk_forward`).

Constrained signal-rule optimization:

```bash
python scripts/optimize_signal_grid.py --db data/synthetic_signal_tune.db --preset smoke --skip-pairs --holdout-frac 0.2
```

See [`docs/signal_rules_examples.md`](docs/signal_rules_examples.md).

---

## Real data (Binance Vision)

Utilities live under `data/binance_vision/` and [`scripts/download_binance_vision.py`](scripts/download_binance_vision.py). Expected schema: [`docs/DATASET.md`](docs/DATASET.md).

Optional env var: `COMPOUND_OPT_DB=/path/to/candles.db`

---

## Main components

| Piece | Role |
|-------|------|
| [`compound_optimize_runner.py`](compound_optimize_runner.py) | Load SQLite, EMA/SMA blend + anti-whipsaw, equity target / ruin, JSON |
| [`leverage_pi.py`](leverage_pi.py) | Optional `pi_ref` policy (PI + smooth reference) |
| [`features/`](features/) | 5m indicators, `--signal-config` rules |
| [`scripts/optimize_signal_grid.py`](scripts/optimize_signal_grid.py) | Signal grid + `p_ruin` / OOS delta gates |
| [`optimization/contract.yaml`](optimization/contract.yaml) | Reference numeric contract |

---

## Not shipped in this public repo

Large sweep artifacts, pitch PDFs, Telegram bots, and other paths listed in `.gitignore` stay local. Versioned under `optimization/`: `contract.yaml`, `contract.json`, `mc_ladder.py`, `verify_run.json`.

---

## Reach & discovery

- Dependabot and CI are enabled; topics and repo description are set on GitHub.
- **Discussions** are enabled for Q&A (prefer over Issues for open questions).
- Share a short technical post (problem → approach → JSON sample + disclaimer) rather than bare repo links.
- PyPI publishing is optional; see [`docs/PUBLISHING_PYPI.md`](docs/PUBLISHING_PYPI.md).

---

## License, security, community

- License: [LICENSE](LICENSE) (MIT).
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md).
- Security: [SECURITY.md](SECURITY.md).
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
