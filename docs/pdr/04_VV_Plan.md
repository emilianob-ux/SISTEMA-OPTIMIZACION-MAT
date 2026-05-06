# 04 — Verification & Validation Plan

## 4.1 Verificación (¿Construimos bien el sistema?)

| Nivel | Alcance | Herramienta | Criterio de aceptación |
|-------|---------|-------------|------------------------|
| **Unitario** | Lógica matemática, validaciones Pydantic, FSM transitions | `pytest`, `hypothesis` | Cobertura de ramas alta en contratos y handlers (objetivo de equipo: 100% en contratos críticos) |
| **Contrato** | Inputs/outputs entre componentes | `pydantic` + `fastapi.testclient` | 0 `ValidationError` no esperadas en payloads válidos; rechazo correcto en inválidos |
| **Integración** | Orchestrator → Redis → GovernanceCore → Skills | `docker-compose` + mocks | Estado recuperado post-reinicio, writes idempotentes |
| **Estático** | Complejidad, dependencias, seguridad | `ruff`, `mypy`, `bandit` | 0 hallazgos críticos; type coverage objetivo >95% en módulos core |

## 4.2 Validación (¿Construimos el sistema correcto?)

| Prueba | Escenario | Métrica de éxito | Responsable |
|--------|-----------|------------------|-------------|
| **Stress Validation** | 200 escenarios compound + shocks de cola | `infeasibility_rate ≤ 5%`, `min_slack ≥ 0.05` | Data Science Lead |
| **Human-in-the-Loop** | Override con ΔKPI > -12%, expiry 24h | Sandbox aprueba, rollback automático al vencimiento | Product/Compliance |
| **Drift Response** | Inyección de cambio de régimen (Frobenius > 0.35) | Detección en ≤3 runs, trigger `CRITICAL`, recalibración | MLOps Eng |
| **Audit Trail** | Simulación de inspección regulatoria | Recuperación de decisión completa en <10s | Legal/Compliance |

## 4.3 Entorno de pruebas

- **Synthetic Data:** Generado con copulas multivariadas, colas pesadas, drift inyectado.
- **Real Data:** Muestra de 90 días de operación histórica (anonimizada).
- **CI/CD:** GitHub Actions → `pytest` → contract tests → deploy staging.
