# Changelog

Format based on Keep a Changelog.

## [Unreleased]

## [0.3.0] - 2026-05-06

### Changed

- Proyecto renombrado a **decision-resilience-engine**: repo GitHub, metadatos PyPI (`pip install decision-resilience-engine`), README y docs de outreach alineados.
- Prioridad narrativa: **DRE** como foco principal; **MAT** como puente de medicion secundario.

### Migration

- PyPI: el paquete **`sistema-optimizacion-mat`** deja de actualizarse en favor de **`decision-resilience-engine`** (nuevo nombre en el indice PyPI).

## [0.2.0] - 2026-05-06

### Added

- Decision Resilience Engine (DRE) MVP under `dre/`.
- DRE API endpoints: `POST /dre/simulate`, `POST /dre/resume`, `GET /dre/health`.
- SQLite governance checkpoints and `DrePipeline.resume_latest`.
- Redis-compatible context store (`RedisContextStore`) plus fakeredis tests.
- MAT bridge command: `dre/measurement/mat_runner.py`.
- Full PDR package in `docs/pdr/` and technical architecture doc.
- `docs/DRE_IMPLEMENTATION_STATUS.md` mapping spec to code.

### Changed

- README and docs index refreshed for MAT + DRE public presentation.
- Dev dependencies expanded with `scipy`, `fastapi`, `uvicorn`, `httpx`, `redis`, `fakeredis`.

### Removed

- Non-essential OSS/community template files removed earlier in this cycle.

## [0.1.4] - 2026-05-06

### Changed

- PyPI workflow supports `workflow_dispatch` with `git_ref` checkout.

## [0.1.3] - 2026-04-27

### Added

- PyPI release workflow (`publish-pypi.yml`).
- `ruff-format` pre-commit hook.

### Changed

- Repo-wide formatting and stricter Ruff config.

## [0.1.2] - 2026-04-27

### Added

- Ruff config, CI lint step, pre-commit baseline.

## [0.1.1] - 2026-04-27

### Added

- English README and quickstart/publishing docs.

## [0.1.0] - 2026-04-28

### Added

- Initial MAT backtesting engine, tests, CI, and docs.
