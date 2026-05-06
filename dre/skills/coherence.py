from __future__ import annotations

from typing import Tuple


def validate_coherence(data_hash: str, execution_mode: str) -> Tuple[bool, str]:
    if not data_hash.startswith("sha256:"):
        return False, "HASH_FORMAT_INVALID"
    if execution_mode not in ("FAST", "STANDARD", "DEEP_AUDIT"):
        return False, "EXECUTION_MODE_INVALID"
    return True, "OK"
