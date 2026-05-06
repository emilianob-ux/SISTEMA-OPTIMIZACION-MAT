# Due diligence / adopción institucional

Resumen corto para equipos que evalúan adopción o fork interno (no sustituye revisión legal).

## Licencia y propiedad

- Licencia **MIT**: [LICENSE](../LICENSE).
- Sin garantías implícitas; uso bajo responsabilidad del usuario.

## Seguridad y reportes

- Política de divulgación responsable: [SECURITY.md](../SECURITY.md).
- No incluir API keys ni rutas a bases privadas en issues públicos.

## Cadena de suministro (Python)

- Dependencias declaradas en `pyproject.toml` / `requirements.txt`; actualizaciones propuestas vía Dependabot.
- Publicación PyPI opcional documentada en [PUBLISHING_PYPI.md](PUBLISHING_PYPI.md) (trusted publishing recomendado).

## Calidad reproducible

- CI ejecuta tests y una corrida mínima del runner sobre una DB sintética generada en el workflow.
- Contrato de métricas y dataset: [DATASET.md](DATASET.md).
- Cambios versionados en [CHANGELOG.md](../CHANGELOG.md).

## Alcance y límites

- Herramienta de **investigación / backtest**; no es asesoramiento financiero ni sistema de ejecución en vivo.
- Artefactos grandes y material comercial deliberadamente fuera del repo público (ver README).

---

## Enterprise readiness (English)

Short checklist for teams assessing adoption or an internal fork (not legal advice).

- **License:** MIT ([LICENSE](../LICENSE)); no warranties.
- **Security:** coordinated disclosure ([SECURITY.md](../SECURITY.md)).
- **Supply chain:** deps in `pyproject.toml` / `requirements.txt`; Dependabot PRs; PyPI flow in [PUBLISHING_PYPI.md](PUBLISHING_PYPI.md).
- **Reproducibility:** CI synthetic DB + tests; metric contract in [DATASET.md](DATASET.md); [CHANGELOG.md](../CHANGELOG.md).
- **Scope:** research/backtest tooling only; not live trading or investment advice.
