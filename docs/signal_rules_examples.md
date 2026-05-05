# Reglas de señal (`--signal-config`) — versión 1

JSON con `version: 1`, `logic`: `"all"` (AND) o `"any"` (OR), y lista `rules`.

**Importante:** las EMA 10–200 de `features/indicators.py` se calculan sobre el **close 5m** del activo. El **cóctel** del runner sigue usando **EMA200 diaria** (y SMA200 4h) mapeadas a la serie 5m. Son construcciones distintas: las reglas `--signal-config` son **filtros adicionales** sobre el mismo precio, no reemplazan el cóctel.

Cada regla es un objeto con `op` y parámetros. Se evalúan **en la misma barra 5m** donde el cóctel ya eligió líder; si falla, no se abre long (el cóctel sigue siendo obligatorio).

## Ops soportadas

| `op` | Parámetros | Notas |
|------|--------------|--------|
| `adx_ge` / `adx_le` | `value` | Si no hay high/low en DB, ADX es NaN → la regla **no pasa** (conservador). |
| `atr_pct_ge` / `atr_pct_le` | `value` | ATR/close; sin H/L se usa proxy solo-close. |
| `bb_width_le` / `bb_width_ge` | `value` | `(upper-lower)/mid`. |
| `bb_pctb_ge` / `bb_pctb_le` | `value` | posición del precio en la banda [0,1]. |
| `dist_close_ema_ge` / `dist_close_ema_le` | `ema_period` (10,20,50,100,200), `value_pct` | `(close-ema)/ema`. |
| `ema_spread_ge` / `ema_spread_le` | `fast`, `slow`, `value_pct_on_close` | `(ema_fast-ema_slow)/close`. |
| `ema_cross_above` / `ema_cross_below` | `fast`, `slow` | |
| `vol_ratio_ge` / `vol_ratio_le` | `value` | `vol/SMA20(vol)-1`; sin volumen en DB ≈ 0. |
| `vol_log_chg_ge` / `vol_log_chg_le` | `value` | `log(vol_t/vol_{t-5})`. |

## Ejemplo 1 — tendencia + volatilidad

```json
{
  "version": 1,
  "logic": "all",
  "rules": [
    { "op": "dist_close_ema_ge", "ema_period": 200, "value_pct": 0.0 },
    { "op": "adx_ge", "value": 18 }
  ]
}
```

## Ejemplo 2 — spread EMA corta vs larga

```json
{
  "version": 1,
  "logic": "all",
  "rules": [
    { "op": "ema_cross_above", "fast": 20, "slow": 100 },
    { "op": "bb_width_le", "value": 0.06 }
  ]
}
```

## Ejemplo 3 — OR (cualquiera de dos filtros)

```json
{
  "version": 1,
  "logic": "any",
  "rules": [
    { "op": "vol_ratio_ge", "value": 0.2 },
    { "op": "atr_pct_ge", "value": 0.02 }
  ]
}
```

## Comando

```text
python compound_optimize_runner.py --db data/candles.db --signal-config ruta/al/archivo.json
```

ADX y Bollinger completos convienen con columnas `high`, `low`, `volume` en `candles` (p. ej. datos Binance Vision normalizados).

---

## Optimización por rejilla (`scripts/optimize_signal_grid.py`)

Barrido acotado: baseline (sin `--signal-config`) + ~40 reglas simples + pares AND entre los mejores singles que pasan gates de **p_ruin** y **|delta ruina OOS−IS|**.

```text
python scripts/optimize_signal_grid.py --db data/candles.db --holdout-frac 0.2 --p-ruin-max 0.58 --max-delta-ruin 0.12
```

Escribe `optimization/signal_grid_<UTC>.json` y, si hay un ganador factible distinto del baseline, `optimization/signal_grid_<UTC>_best_config.json` listo para `--signal-config`.

Argumentos útiles: `--workers 4`, `--skip-pairs` (solo singles), `--max-pairs 20`, y args extra al runner al final, p. ej. `--lev1 8 --t1 250`.

**Rendimiento:** con `--in-process` (por defecto) los datos se cargan **una sola vez**; evita `--workers` altos en in-process (el bucle ya es secuencial).

**DB sintética de prueba** (sin `candles.db` real):

```text
python scripts/bootstrap_synthetic_candles_db.py
python scripts/optimize_signal_grid.py --db data/synthetic_signal_tune.db --preset full --holdout-frac 0.2
```

O en un solo paso: `--allow-bootstrap` si no existe ninguna DB resuelta (prioriza `data/candles.db` y el repo hermano `BOTS TRADING` si están).
