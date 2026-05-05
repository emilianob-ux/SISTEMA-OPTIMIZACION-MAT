"""Carga OHLCV desde SQLite alineado por timestamp (BTC/ETH)."""

from __future__ import annotations

import sqlite3

import numpy as np


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1].lower() for r in rows}


def load_btc_eth_series(
    db_path: str,
    start_ts: int = 1567296000000,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray | None,
    np.ndarray | None,
    np.ndarray | None,
    np.ndarray | None,
    np.ndarray | None,
    np.ndarray | None,
]:
    """
    Devuelve (cl_b, cl_e, hi_b, lo_b, vo_b, hi_e, lo_e, vo_e).
    Si faltan columnas, high=low=close y volume=None (indicadores degradan con aviso en caller).
    """
    co = sqlite3.connect(db_path)
    cols = _table_columns(co, "candles")
    need = {"timestamp", "close", "symbol"}
    if not need.issubset(cols):
        co.close()
        raise RuntimeError(f"Tabla candles no tiene columnas mínimas: {need}")

    has_hl = "high" in cols and "low" in cols
    has_vol = "volume" in cols

    sel = ["timestamp", "close"]
    if has_hl:
        sel.extend(["high", "low"])
    if has_vol:
        sel.append("volume")

    q = f"SELECT {','.join(sel)} FROM candles WHERE symbol=? AND timestamp>=? ORDER BY timestamp"

    def fetch(sym: str):
        rows = co.execute(q, (sym, start_ts)).fetchall()
        ts = np.array([r[0] for r in rows], dtype=np.int64)
        cl = np.array([float(r[1]) for r in rows], dtype=np.float64)
        if has_hl:
            hi = np.array([float(r[2]) for r in rows], dtype=np.float64)
            lo = np.array([float(r[3]) for r in rows], dtype=np.float64)
            off = 4
        else:
            hi = lo = cl.copy()
            off = 2
        if has_vol:
            vo = np.array([float(r[off]) for r in rows], dtype=np.float64)
        else:
            vo = None
        return ts, cl, hi, lo, vo

    ts_b, cl_b, hi_b, lo_b, vo_b = fetch("BTCUSDT")
    ts_e, cl_e, hi_e, lo_e, vo_e = fetch("ETHUSDT")
    co.close()

    n = min(len(cl_b), len(cl_e))
    cl_b = cl_b[:n]
    cl_e = cl_e[:n]
    hi_b = hi_b[:n]
    lo_b = lo_b[:n]
    hi_e = hi_e[:n]
    lo_e = lo_e[:n]
    if vo_b is not None:
        vo_b = vo_b[:n]
    if vo_e is not None:
        vo_e = vo_e[:n]

    if not has_hl:
        hi_b = lo_b = hi_e = lo_e = None
    if not has_vol:
        vo_b = vo_e = None

    return cl_b, cl_e, hi_b, lo_b, vo_b, hi_e, lo_e, vo_e
