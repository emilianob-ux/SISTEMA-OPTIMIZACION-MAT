# 03 — Risk Register

| ID | Riesgo | Categoría | Prob. (1-5) | Impacto (1-5) | RPN | Mitigación | Trigger / Owner | Contingencia |
|----|--------|-----------|-------------|---------------|-----|------------|-----------------|--------------|
| **R-01** | Solver timeout en LP relaxation (Backprop) | Técnico | 3 | 4 | 12 | Timebox 2s, fallback a `REFORMULATION_INFEASIBLE` | Timeout >2s / DevOps | Escalar a `ESCALATED`, notificar al humano |
| **R-02** | Pérdida de estado Redis durante pausa prolongada | Operativo | 2 | 4 | 8 | Snapshot a GovernanceCore antes de `ESCALATED` | Redis TTL expirado / SRE | Forzar recomputo desde checkpoint o inicio |
| **R-03** | Datos históricos insuficientes para PSI/Frobenius | Datos | 4 | 3 | 12 | Política cold start + `WARNING_EARLY` | `n_available < threshold` / Data Eng | Usar distribución training + alertar al usuario |
| **R-04** | Override humano viola restricciones HARD | Seguridad | 1 | 5 | 5 | Sandbox + validación LP/bounds pre-aplicación | Bounds check fail / Security | Rechazar automáticamente, log de intento |
| **R-05** | Auditoría no cumple EU AI Act / SR 11-7 | Cumplimiento | 2 | 5 | 10 | Trazabilidad `data_hash`, `run_id_hash`, append-only | Revisión legal pre-deploy / Compliance | Pausar despliegue, ajustar logging |
| **R-06** | Loop infinito por `iteration_count` no persistido | Arquitectónico | 1 | 5 | 5 | Persistencia obligatoria en Redis/GovernanceCore | `iteration_count` no se actualiza / Backend Dev | Fail-safe: hard cap en orquestador |
