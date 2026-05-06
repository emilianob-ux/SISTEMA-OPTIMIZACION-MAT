# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [Unreleased]

### Añadido

- Paquete PDR del **Decision Resilience Engine** bajo `docs/pdr/` (01–05).
- Documento [`docs/DRE_TECHNICAL_ARCHITECTURE.md`](docs/DRE_TECHNICAL_ARCHITECTURE.md) v1.1 (fundamentos, pipelines, diagramas Mermaid, stack).
- Paquete [`dre/contracts/`](dre/contracts/) con modelos Pydantic alineados al ICD; tests en `tests/test_dre_contracts.py`.
- Dependencia de desarrollo `pydantic>=2,<3`; índice [`docs/README.md`](docs/README.md).

### Eliminado

- Plantillas de issue, plantilla de PR, Dependabot, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CITATION.cff`, `README.en.md`.
- Documentación y material de planificación no necesarios para ejecutar el proyecto: `docs/brainstorms/`, `docs/ideation/`, `docs/specs/`, `docs/ENTERPRISE_READINESS.md`, `docs/PUBLISHING_PYPI.md`, `docs/examples/`, `docs/ce-optimize-spec.yaml` (queda `ce-optimize-spec.yaml` en la raíz). El índice `docs/README.md` se reintroduce como tabla de contenidos MAT + DRE.

### Cambiado

- `README.md` reducido al uso operativo del repo; `docs/tutorial_quickstart.md` sin referencia al README en inglés.
- Sección **Decision Resilience Engine** en README enlazando PDR + arquitectura técnica + `dre/`.

## [0.1.4] — 2026-05-06

### Cambiado

- Workflow PyPI: disparador manual `workflow_dispatch` con input `git_ref` y checkout seguro según evento.
- Docs `PUBLISHING_PYPI.md`: enlace a la página de *account publishing* de PyPI y cómo recrear el entorno `pypi` en GitHub vía `gh api`.

## [0.1.3] — 2026-04-27

### Añadido

- Workflow `.github/workflows/publish-pypi.yml` para publicar en PyPI al crear un **Release** (trusted publishing).
- Hook `ruff-format` en `.pre-commit-config.yaml`.

### Cambiado

- Formato con `ruff format` en el código Python versionado; imports ordenados (`I001`); líneas largas (`E501`) corregidas donde aplicaba.
- Se eliminan los ignores globales `E501`/`I001` en Ruff; permanece exclusión local `E701`/`E702` solo en `compound_optimize_runner.py`.
- `pyproject.toml`: licencia SPDX `MIT`; CI ejecuta `ruff format --check .`; `.gitignore` incluye `dist/` y `build/`.

## [0.1.2] — 2026-04-27

### Añadido

- Configuración Ruff (`pyproject.toml`), paso `ruff check` en CI y `.pre-commit-config.yaml` (hook `ruff`).
- `docs/README.md` como índice de documentación.
- Dependencias de desarrollo: `ruff`, `pre-commit`.

### Cambiado

- Plantillas de issue: etiquetas por defecto `bug` / `enhancement`.
- Badges de Python y licencia en README (ES/EN).
- Primera pasada Ruff en CI; `compound_optimize_runner.py` mantiene exclusión `E701`/`E702` (ver endurecimiento en 0.1.3).

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
