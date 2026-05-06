# Contribuir

Gracias por interesarte en mejorar este proyecto.

## Antes de abrir un PR

1. Ejecutá CI localmente:
   - `pip install -r requirements.txt -r requirements-dev.txt`  
     (equivalente: `pip install -e ".[dev]"` desde la raíz del repo)
   - `python scripts/bootstrap_synthetic_candles_db.py`
   - `pytest tests/`
   - `python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0 | python -c "import json,sys; json.load(sys.stdin)"`
   - `ruff check .` y `ruff format --check .` (lo mismo aplican los hooks de pre-commit).

2. Opcional: instalá hooks locales — `pre-commit install` y `pre-commit run --all-files` (usa `.pre-commit-config.yaml`).

3. Mantené los cambios **acotados** al problema (sin refactors masivos salvo que acuerden en un issue).

4. Si tocás contratos numéricos (ruina, ventanas, métricas), documentá el cambio en el README o en `docs/`.

## Issues

- Incluí SO, versión de Python y comando exacto que falla.
- Para bugs de backtest: pegá un fragmento del JSON de salida (sin datos privados).

Etiquetas estándar del repo: `bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`, `question`. Para empezar a contribuir, buscá **`good first issue`**.

Tutorial para reproducir el stack local: [`docs/tutorial_quickstart.md`](docs/tutorial_quickstart.md).

## Código

- Python 3.11+ recomendado (CI usa 3.12).
- Preferí tipos y nombres que encajen con `compound_optimize_runner.py` y `features/`.
