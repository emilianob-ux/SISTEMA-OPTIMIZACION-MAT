from __future__ import annotations

import unittest

from pydantic import ValidationError

from dre.contracts import ExecutionContext, StressFeedbackPayload


class TestDREContracts(unittest.TestCase):
    def test_stress_feedback_valid(self) -> None:
        p = StressFeedbackPayload(
            failed_constraints=["c1"],
            stress_scenarios_failed=["s1"],
            slack_violation_magnitude={"x": "0.1"},
            recommended_action="add_robustness_buffer",
            action_priority=["add_robustness_buffer", "relax_soft_with_penalty"],
        )
        self.assertTrue(p.robustness_backpropagation_triggered)

    def test_stress_feedback_rejects_mismatch(self) -> None:
        with self.assertRaises(ValidationError):
            StressFeedbackPayload(
                failed_constraints=[],
                stress_scenarios_failed=[],
                slack_violation_magnitude={},
                recommended_action="switch_to_stochastic",
                action_priority=["relax_soft_with_penalty"],
            )

    def test_execution_context_run_id_pattern(self) -> None:
        ctx = ExecutionContext(
            run_id="opt_20250418_143022_v5.0",
            execution_mode="STANDARD",
            current_state="IDLE",
            iteration_count=0,
        )
        self.assertEqual(ctx.execution_mode, "STANDARD")

        with self.assertRaises(ValidationError):
            ExecutionContext(
                run_id="bad_id",
                execution_mode="FAST",
                current_state="ROUTING",
                iteration_count=0,
            )
