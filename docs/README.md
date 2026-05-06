# Documentacion

Repositorio **`decision-resilience-engine`**: Decision Resilience Engine (DRE) como eje principal; MAT como puente de medicion cuantitativa.

## DRE (Decision Resilience Engine)

Este repositorio incluye especificacion + implementacion MVP del DRE.

| Documento | Contenido |
|-----------|-----------|
| [pdr/README.md](pdr/README.md) | Paquete PDR (01-05) para comite tecnico. |
| [DRE_TECHNICAL_ARCHITECTURE.md](DRE_TECHNICAL_ARCHITECTURE.md) | Arquitectura tecnica v1.1 (fundamentos, Mermaid, stack). |
| [DRE_IMPLEMENTATION_STATUS.md](DRE_IMPLEMENTATION_STATUS.md) | Mapa especificacion <-> codigo y backlog. |

## MAT (simulacion y optimizacion — medicion secundaria)

| Documento | Contenido |
|-----------|-----------|
| [tutorial_quickstart.md](tutorial_quickstart.md) | Entorno, DB sintetica, tests y corrida del runner. |
| [DATASET.md](DATASET.md) | Esquema SQLite esperado (velas + funding). |
| [signal_rules_examples.md](signal_rules_examples.md) | Ejemplos de `--signal-config` en JSON. |

## Publicacion PyPI

| Documento | Contenido |
|-----------|-----------|
| [PUBLISHING_PYPI.md](PUBLISHING_PYPI.md) | Trusted Publisher + workflow `publish-pypi.yml` + release/tag. |

## Go-to-market / alcance

| Documento | Contenido |
|-----------|-----------|
| [LAUNCH_KIT.md](LAUNCH_KIT.md) | Copy listo para publicar + plan de distribucion. |
| [OUTREACH_EXECUTION.md](OUTREACH_EXECUTION.md) | Plan 7 dias por canal + KPI framework. |
| [LAUNCH_DAY_CHECKLIST.md](LAUNCH_DAY_CHECKLIST.md) | Checklist operativo para el dia de lanzamiento. |

Codigo relacionado:

- [`dre/`](../dre/README.md): orquestador, governance, storage, skills, API.
- [`scripts/run_dre_api.py`](../scripts/run_dre_api.py): arranque local del servicio.
