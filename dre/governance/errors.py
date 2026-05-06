from __future__ import annotations


class RunIdCollisionError(RuntimeError):
    """`run_id` repetido con `data_hash` distinto (ICD §6.1)."""

    def __init__(self, run_id: str, data_hash_expected: str, data_hash_received: str) -> None:
        super().__init__("RUN_ID_COLLISION")
        self.run_id = run_id
        self.data_hash_expected = data_hash_expected
        self.data_hash_received = data_hash_received

    def as_json(self) -> dict:
        return {
            "error": "RUN_ID_COLLISION",
            "detail": "Same run_id with different data_hash detected",
            "run_id": self.run_id,
            "data_hash_expected": self.data_hash_expected,
            "data_hash_received": self.data_hash_received,
            "recovery": "Generate new run_id or verify input pipeline consistency",
        }
