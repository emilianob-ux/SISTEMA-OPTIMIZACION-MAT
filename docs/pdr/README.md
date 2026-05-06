# Paquete PDR — Decision Resilience Engine

**Sistema:** Decision Resilience Engine (DRE)  
**Versión PDR:** 1.0 · **Revisión:** lista para comité de ingeniería  
**Baseline:** especificaciones ecosystem v1.5–v1.8  

Este directorio contiene el **Preliminary Design Review (PDR)** en archivos independientes, listos para wiki, Confluence o revisión en GitHub/GitLab.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| [01_Requirements_Traceability_Matrix.md](01_Requirements_Traceability_Matrix.md) | Matriz de trazabilidad FR/NFR → componentes y verificación. |
| [02_Interface_Contracts_ICD.md](02_Interface_Contracts_ICD.md) | Contratos de interfaz (ICD), payloads Pydantic y errores tipados. |
| [03_Risk_Register.md](03_Risk_Register.md) | Registro de riesgos, RPN, mitigaciones y owners. |
| [04_VV_Plan.md](04_VV_Plan.md) | Plan de verificación y validación (unitario → auditoría). |
| [05_PDR_Review_Checklist.md](05_PDR_Review_Checklist.md) | Checklist Go/No-Go, open issues, firmas. |

## Arquitectura técnica ampliada

Fundamentos matemáticos, diagramas Mermaid y stack de implementación: [**DRE_TECHNICAL_ARCHITECTURE.md**](../DRE_TECHNICAL_ARCHITECTURE.md) (v1.1, alineado con specs v1.5–v1.8).

## Relación con este repositorio (MAT)

- **`sistema-optimizacion-mat`** en este repo = implementación del **simulador / medición** en dominio futuros compuesto (SQLite, métricas `p_ruin`, walk-forward, rejillas de señales).
- El **DRE** define el **orquestador**, stress formalizado Optimizer→Stress→Backprop, governance append-only, overrides humanos, drift continuo, etc.
- Integración prevista: el runner MAT puede actuar como **comando de medición** dentro del pipeline DRE (patrón tipo “measurement.command”), sin confundir el alcance del paquete PyPI actual con el motor completo del DRE.

## Uso sugerido

1. Revisar los cinco archivos del PDR en orden numérico.
2. Cruzar con [DRE_TECHNICAL_ARCHITECTURE.md](../DRE_TECHNICAL_ARCHITECTURE.md) para diagramas y complejidades.
3. Archivar como `PDR_v1.0_APPROVED` tras firma de checklist `05`.
4. Avanzar a **CDR (Critical Design Review)** con diseño detallado por componente.
