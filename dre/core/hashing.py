from __future__ import annotations

import hashlib


def sha256_text(payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
