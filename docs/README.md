# Documentacion

## MAT (simulacion y optimizacion)

| Documento | Contenido |
|-----------|-----------|
| [tutorial_quickstart.md](tutorial_quickstart.md) | Entorno, DB sintetica, tests y corrida del runner. |
| [DATASET.md](DATASET.md) | Esquema SQLite esperado (velas + funding). |
| [signal_rules_examples.md](signal_rules_examples.md) | Ejemplos de `--signal-config` en JSON. |

## DRE (Decision Resilience Engine)

Este repositorio incluye especificacion + implementacion MVP del DRE.

| Documento | Contenido |
|-----------|-----------|
| [pdr/README.md](pdr/README.md) | Paquete PDR (01-05) para comite tecnico. |
| [DRE_TECHNICAL_ARCHITECTURE.md](DRE_TECHNICAL_ARCHITECTURE.md) | Arquitectura tecnica v1.1 (fundamentos, Mermaid, stack). |
| [DRE_IMPLEMENTATION_STATUS.md](DRE_IMPLEMENTATION_STATUS.md) | Mapa especificacion <-> codigo y backlog. |
| [LAUNCH_KIT.md](LAUNCH_KIT.md) | Ready-to-post launch copy + 7-day distribution plan. |

Codigo relacionado:

- [`dre/`](../dre/README.md): orquestador, governance, storage, skills, API.
- [`scripts/run_dre_api.py`](../scripts/run_dre_api.py): arranque local del servicio.
