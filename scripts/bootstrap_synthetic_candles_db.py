"""
Genera data/synthetic_signal_tune.db con BTC/ETH 5m OHLCV + funding en cero,
solo para pruebas del optimizador de señales cuando no hay candles.db real.

~24k barras (~52 días de 5m) -> pocas ventanas deslizantes; resultados numéricos
no tienen interpretación de mercado, solo validan el pipeline.
"""

from __future__ import annotations

import json
import os
import sqlite3

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_ROOT, "data", "synthetic_signal_tune.db")
START_TS = 1567296000000
BAR_MS = 300000  # 5m
N = 24500  # ~nw ≈ 25 ventanas con w=17280, step=288


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.isfile(OUT):
        os.remove(OUT)
    rng = np.random.default_rng(42)
    n = N
    ts = START_TS + np.arange(n, dtype=np.int64) * BAR_MS
    # Random walk log-prices
    rb = np.exp(np.cumsum(rng.normal(0, 0.0008, n))) * 10000.0
    re = np.exp(np.cumsum(rng.normal(0, 0.0009, n))) * 3000.0
    # OHLC sintético alrededor del close
    hb = rb * (1.0 + rng.uniform(0, 0.002, n))
    lb_ = rb * (1.0 - rng.uniform(0, 0.002, n))
    ob = rb * (1.0 + rng.uniform(-0.001, 0.001, n))
    he = re * (1.0 + rng.uniform(0, 0.002, n))
    le = re * (1.0 - rng.uniform(0, 0.002, n))
    oe = re * (1.0 + rng.uniform(-0.001, 0.001, n))
    vb = np.abs(rng.normal(500, 150, n)) + 1.0
    ve = np.abs(rng.normal(400, 120, n)) + 1.0

    con = sqlite3.connect(OUT)
    con.execute(
        "CREATE TABLE candles (timestamp INTEGER, symbol TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL)"
    )
    con.execute("CREATE TABLE funding (timestamp INTEGER, symbol TEXT, fundingRate REAL)")
    def row_pack(o, h, l_, c, v, sym: str):
        rows = []
        for i in range(n):
            rows.append(
                (
                    int(ts[i]),
                    sym,
                    float(o[i]),
                    float(h[i]),
                    float(l_[i]),
                    float(c[i]),
                    float(v[i]),
                )
            )
        return rows

    rows_b = row_pack(ob, hb, lb_, rb, vb, "BTCUSDT")
    rows_e = row_pack(oe, he, le, re, ve, "ETHUSDT")
    con.executemany(
        "INSERT INTO candles VALUES (?,?,?,?,?,?,?)",
        rows_b,
    )
    con.executemany("INSERT INTO candles VALUES (?,?,?,?,?,?,?)", rows_e)
    con.executemany(
        "INSERT INTO funding VALUES (?,?,?)",
        [(int(ts[i]), "BTCUSDT", 0.0) for i in range(n)]
        + [(int(ts[i]), "ETHUSDT", 0.0) for i in range(n)],
    )
    con.commit()
    con.close()
    print(json.dumps({"wrote": OUT, "bars": n}, indent=2))


if __name__ == "__main__":
    main()
