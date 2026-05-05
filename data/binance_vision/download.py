"""Descarga HTTP de zips (sin autenticacion)."""

from __future__ import annotations

from typing import Optional

import requests

DEFAULT_TIMEOUT_S = 120
DEFAULT_USER_AGENT = "SISTEMA-OPTIMIZACION-MAT-binance-vision/1.0"


def download_bytes(
    url: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    session: Optional[requests.Session] = None,
) -> bytes:
    """Descarga el recurso completo en memoria. Lanza si el status no es 200."""
    sess = session or requests.Session()
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    r = sess.get(url, headers=headers, timeout=timeout_s)
    r.raise_for_status()
    return r.content
