# 01 — Requirements Traceability Matrix

**Sistema:** Decision Resilience Engine  
**Versión PDR:** 1.0 | **Revisión:** Engineering Committee Ready  
**Alcance:** Validación de arquitectura, contratos, riesgos, V&V y estructura de aprobación  
**Baseline:** Especificaciones v1.5–v1.8 aprobadas  

| ID | Requisito | Tipo | Componente Responsable | Diseño Espec. | Método de Verificación | Estado |
|----|-----------|------|------------------------|---------------|------------------------|--------|
| **FR-01** | Generar distribuciones probabilísticas con IC90/IC95 | Funcional | `ProbabilisticForecasting` | §1–§3 | Test de bondad de ajuste (KS/AD) + validación de CV | Diseñado |
| **FR-02** | Validar solución contra ≥50 escenarios de estrés | Funcional | `SimulationStressTest` | §1–§5 | Métricas de infactibilidad, slack, degradación KPI | Diseñado |
| **FR-03** | Auto-reformulación ≤2 intentos antes de escalar | Funcional | `RobustnessBackpropagation` | §2–§4 | Conteo de `iteration_count`, validación LP timebox | Diseñado |
| **FR-04** | Intervención humana con sandbox y time-bound expiry | Funcional | `HumanOverrideProtocol` | §1–§5 | ΔKPI thresholds, TTL enforcement, replay prevention | Diseñado |
| **FR-05** | Detección de drift con PSI, Frobenius y KPI σ | Funcional | `ModelMonitoringDriftDetector` | §1–§5 | Ventanas deslizantes, regla de 3 runs consecutivos | Diseñado |
| **NFR-01** | Latencia <30s (STANDARD), <2s (FAST) | No Funcional | Orchestrator + Skills | §7 | Load testing, profiling de solver | Pendiente |
| **NFR-02** | Trazabilidad inmutable (append-only, `data_hash`) | No Funcional | `LightweightGovernanceCore` | §4–§6 | Test de inmutabilidad, auditoría de writes | Diseñado |
| **NFR-03** | Recuperación de estado tras fallo (Redis TTL 72h) | No Funcional | Orchestrator FSM | §5.1 | Inyección de fallo, verificación de restore | Pendiente |
| **NFR-04** | Cumplimiento EU AI Act / SR 11-7 (auditoría 1-clic) | No Funcional | GovernanceCore + Override | §6 | Revisión legal + mock de inspección regulatoria | Pendiente |

---

*Referencias de diseño detallado: ver [DRE_TECHNICAL_ARCHITECTURE.md](../DRE_TECHNICAL_ARCHITECTURE.md) y [02_Interface_Contracts_ICD.md](02_Interface_Contracts_ICD.md).*
