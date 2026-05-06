# Documentación

## Uso del repo MAT (backtest / optimización de señales)

| Documento | Contenido |
|-----------|-----------|
| [tutorial_quickstart.md](tutorial_quickstart.md) | Entorno, DB sintética, tests, corrida del runner. |
| [DATASET.md](DATASET.md) | Esquema SQLite esperado (velas + funding). |
| [signal_rules_examples.md](signal_rules_examples.md) | Ejemplos de `--signal-config` en JSON. |

## Decision Resilience Engine (DRE) — especificación

La visión de producto **Decision Resilience Engine** y el paquete **PDR** viven en [`pdr/`](pdr/README.md). El código Python de este repositorio implementa hoy el **motor MAT** (simulación compuesta); el DRE completo (orquestador, Redis, governance, causal, drift como servicio, etc.) está **especificado** ahí para diseño e implementación futura o en un repo hermano.

| Documento | Contenido |
|-----------|-----------|
| [pdr/README.md](pdr/README.md) | Índice del paquete PDR + relación con MAT. |
| [DRE_TECHNICAL_ARCHITECTURE.md](DRE_TECHNICAL_ARCHITECTURE.md) | Arquitectura técnica v1.1 (fundamentos, pipelines, Mermaid, stack). |
| [DRE_IMPLEMENTATION_STATUS.md](DRE_IMPLEMENTATION_STATUS.md) | Qué está implementado en `dre/` vs pendiente. |
