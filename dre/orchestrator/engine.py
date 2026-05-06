from __future__ import annotations

from dataclasses import asdict

import numpy as np

from dre.contracts.orchestrator_context import ExecutionContext
from dre.governance.sqlite_store import SqliteGovernanceStore
from dre.orchestrator.fsm import resolve_transition
from dre.skills.causal import propensity_overlap_1d, tier1_gate
from dre.skills.coherence import validate_coherence
from dre.skills.forecasting import fit_univariate_series
from dre.skills.stress import stress_lp_batch
from dre.storage.memory import MemoryContextStore


class DrePipeline:
    """Orquestación MVP: FSM determinística + skills numéricos + bitácora SQLite."""

    def __init__(
        self,
        governance: SqliteGovernanceStore,
        memory: MemoryContextStore | None = None,
    ) -> None:
        self.gov = governance
        self.memory = memory if memory is not None else MemoryContextStore()

    def advance(self, ctx: ExecutionContext, event: str) -> ExecutionContext:
        before = ctx.current_state
        after_state = resolve_transition(before, event)
        new_ctx = ctx.model_copy(update={"current_state": after_state})
        self.gov.append_audit(
            ctx.run_id,
            event,
            state_before=before,
            state_after=after_state,
            payload={},
        )
        self.memory.save(new_ctx)
        return new_ctx

    def simulate_standard_success(
        self, run_id: str, data_hash: str, *, rng_seed: int = 42
    ) -> ExecutionContext:
        """Camino feliz STANDARD sin intervención causal."""
        reg_status = self.gov.write_run(run_id, data_hash, {"scenario": "standard_success"})
        ctx = ExecutionContext(
            run_id=run_id,
            execution_mode="STANDARD",
            current_state="IDLE",
            iteration_count=0,
            skill_statuses={"registry_write": reg_status},
        )

        ctx = self.advance(ctx, "REQUEST_RECEIVED")
        ctx = self.advance(ctx, "CLASSIFIED")

        ok, _reason = validate_coherence(data_hash, ctx.execution_mode)
        ctx = self.advance(ctx, "VALIDATION_PASS" if ok else "VALIDATION_BLOCKED")
        if ctx.current_state == "FAILED":
            return ctx

        rng = np.random.default_rng(rng_seed)
        samples = rng.normal(loc=1.0, scale=0.05, size=200)
        fc = fit_univariate_series(samples)
        ctx = ctx.model_copy(update={"skill_statuses": {**ctx.skill_statuses, "forecasting": fc}})

        ctx = self.advance(ctx, "FORECAST_SKIP_CAUSAL")

        ctx = self.advance(ctx, "OPTIMIZATION_READY")
        ctx = self.advance(ctx, "PARTIAL_GOVERNANCE_DONE")

        c = np.array([1.0, 1.0])
        a_ub = np.array([[1.0, 1.0]])
        b_ub = np.array([3.0])
        deltas = [np.array([0.0]), np.array([-0.2]), np.array([-0.5])]
        stress = stress_lp_batch(c, a_ub, b_ub, deltas)
        ctx = ctx.model_copy(
            update={"skill_statuses": {**ctx.skill_statuses, "stress": asdict(stress)}}
        )

        ctx = self.advance(ctx, "STRESS_PASS")
        ctx = self.advance(ctx, "FINAL_GOVERNANCE_DONE")
        ctx = self.advance(ctx, "DEPLOY_MONITOR")
        return ctx

    def simulate_intervention_success(
        self, run_id: str, data_hash: str, *, rng_seed: int = 7
    ) -> ExecutionContext:
        """Camino con paso causal Tier-1 (overlap alto)."""
        reg_status = self.gov.write_run(run_id, data_hash, {"scenario": "intervention_success"})
        ctx = ExecutionContext(
            run_id=run_id,
            execution_mode="STANDARD",
            current_state="IDLE",
            iteration_count=0,
            skill_statuses={"registry_write": reg_status},
        )

        ctx = self.advance(ctx, "REQUEST_RECEIVED")
        ctx = self.advance(ctx, "CLASSIFIED")

        ok, _ = validate_coherence(data_hash, ctx.execution_mode)
        ctx = self.advance(ctx, "VALIDATION_PASS" if ok else "VALIDATION_BLOCKED")
        if ctx.current_state == "FAILED":
            return ctx

        rng = np.random.default_rng(rng_seed)
        fc = fit_univariate_series(rng.normal(0.5, 0.08, size=180))
        ctx = ctx.model_copy(update={"skill_statuses": {**ctx.skill_statuses, "forecasting": fc}})
        ctx = self.advance(ctx, "FORECAST_NEED_CAUSAL")

        treated = rng.normal(1.0, 0.1, size=500)
        control = rng.normal(1.0, 0.1, size=500)
        overlap = propensity_overlap_1d(treated, control)
        gate = tier1_gate(overlap)
        ctx = ctx.model_copy(
            update={
                "skill_statuses": {
                    **ctx.skill_statuses,
                    "causal": {"overlap": overlap, "gate": gate},
                }
            }
        )
        ctx = self.advance(ctx, "CAUSAL_PASS" if gate == "PASS" else "CAUSAL_BLOCKED")
        if ctx.current_state == "ESCALATED":
            return ctx

        ctx = self.advance(ctx, "OPTIMIZATION_READY")
        ctx = self.advance(ctx, "PARTIAL_GOVERNANCE_DONE")

        c = np.array([1.0, 1.0])
        a_ub = np.array([[1.0, 1.0]])
        b_ub = np.array([3.0])
        deltas = [np.array([0.0]), np.array([-0.1])]
        stress = stress_lp_batch(c, a_ub, b_ub, deltas)
        ctx = ctx.model_copy(
            update={"skill_statuses": {**ctx.skill_statuses, "stress": asdict(stress)}}
        )
        ctx = self.advance(ctx, "STRESS_PASS")
        ctx = self.advance(ctx, "FINAL_GOVERNANCE_DONE")
        ctx = self.advance(ctx, "DEPLOY_MONITOR")
        return ctx
