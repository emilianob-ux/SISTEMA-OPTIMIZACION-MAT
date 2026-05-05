# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [0.1.2] — 2026-04-27

### Añadido

- Configuración Ruff (`pyproject.toml`), paso `ruff check` en CI y `.pre-commit-config.yaml` (hook `ruff`).
- `docs/README.md` como índice de documentación.
- Dependencias de desarrollo: `ruff`, `pre-commit`.

### Cambiado

- Plantillas de issue: etiquetas por defecto `bug` / `enhancement`.
- Badges de Python y licencia en README (ES/EN).
- Reglas Ruff pragmáticas: `E501`/`I001` ignorados por ahora para no masificar el árbol; `compound_optimize_runner.py` sigue con exclusión de `E701`/`E702`.

### Comunidad (GitHub)

- Discussions habilitadas en el repositorio.

## [0.1.1] — 2026-04-27

### Añadido

- `README.en.md`, `docs/tutorial_quickstart.md`, `docs/PUBLISHING_PYPI.md`.

### Cambiado

- CI: `actions/checkout@v6`, `actions/setup-python@v6` (runtime Node 24).

## [0.1.0] — 2026-04-28

### Añadido

- README orientado a reproducibilidad, CI, dataset documentado.
- Reglas de señal JSON (`--signal-config`), optimizador por rejilla (`scripts/optimize_signal_grid.py`).
- Tests (`pytest`) y workflow GitHub Actions.
- Dependabot para dependencias pip y GitHub Actions.
- Metadatos del proyecto en `pyproject.toml`.
