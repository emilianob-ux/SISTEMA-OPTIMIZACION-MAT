# Dataset SQLite (`candles.db`)

El runner espera **SQLite** con al menos estas tablas.

## Tabla `candles`

Columnas usadas por `compound_optimize_runner.load_data` y `features.loaders`:

| Columna | Tipo | Obligatorio |
|---------|------|-------------|
| `timestamp` | INTEGER (ms UTC) | sí |
| `symbol` | TEXT (`BTCUSDT`, `ETHUSDT`) | sí |
| `close` | REAL | sí |
| `high`, `low` | REAL | opcional (sin ellos: ADX clásico no disponible; ATR proxy solo-close) |
| `volume` | REAL | opcional (sin él: features de volumen quedan neutras) |
| `open` | REAL | opcional (no usado por el runner core) |

Las filas **BTC** y **ETH** deben estar **alineadas**: mismo conjunto de `timestamp` en el mismo orden (el código trunca a la longitud mínima).

Esquema mínimo viable:

```sql
CREATE TABLE candles (
  timestamp INTEGER NOT NULL,
  symbol TEXT NOT NULL,
  close REAL NOT NULL
);
CREATE INDEX idx_candles_sym_ts ON candles(symbol, timestamp);
```

Para OHLCV completo (recomendado para reglas ADX/Bollinger):

```sql
CREATE TABLE candles (
  timestamp INTEGER NOT NULL,
  symbol TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL NOT NULL,
  volume REAL
);
```

## Tabla `funding`

```sql
CREATE TABLE funding (
  timestamp INTEGER NOT NULL,
  symbol TEXT NOT NULL,
  fundingRate REAL NOT NULL
);
```

Si falta un timestamp en funding, el costo se trata como **0** para esa barra.

## Construir datos

1. **Sintético (CI / demos):** `python scripts/bootstrap_synthetic_candles_db.py` → `data/synthetic_signal_tune.db`
2. **Binance Vision:** ver `scripts/download_binance_vision.py` y `data/binance_vision/` (normalización propia del repo).
