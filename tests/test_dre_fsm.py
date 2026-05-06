from __future__ import annotations

import unittest

from dre.orchestrator.errors import FSMError
from dre.orchestrator.fsm import resolve_transition


class TestDREFSM(unittest.TestCase):
    def test_happy_subset(self) -> None:
        self.assertEqual(resolve_transition("IDLE", "REQUEST_RECEIVED"), "ROUTING")
        self.assertEqual(resolve_transition("ROUTING", "CLASSIFIED"), "VALIDATING")
        self.assertEqual(resolve_transition("STRESS_TESTING", "STRESS_PASS"), "GOVERNING_FINAL")

    def test_invalid_transition(self) -> None:
        with self.assertRaises(FSMError):
            resolve_transition("IDLE", "CLASSIFIED")
