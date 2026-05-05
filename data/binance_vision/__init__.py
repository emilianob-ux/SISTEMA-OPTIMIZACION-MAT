"""
Descarga y normalizacion de datos publicos de Binance (data.binance.vision).

Origen HTTPS (S3/CloudFront): ``https://data.binance.vision/``

Patrones de URL usados (futures USD-M, ``um``):

- **Funding (mensual):**
  ``/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY-MM}.zip``

- **Klines mensuales:**
  ``/data/futures/um/monthly/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{YYYY-MM}.zip``

- **Klines diarios:**
  ``/data/futures/um/daily/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{YYYY-MM-DD}.zip``

Integracion futura con backtest / ``fine_tune_test`` (Hydra u otro orquestador):

- Tras ejecutar la CLI o ``python -m data.binance_vision``, los CSV normalizados
  quedan bajo ``data/cache/binance_vision/`` (configurable con ``--cache-dir``).
- **Funding:** ``.../futures_um/funding/{SYMBOL}/{SYMBOL}_funding_{YYYY-MM}.csv``
  con columnas ``symbol,calc_time_ms,funding_interval_hours,funding_rate``.
- **Klines:** ``.../futures_um/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}_{INTERVAL}_{periodo}.csv``
  con columnas OHLCV y tiempos en ms (ver ``NORMALIZED_KLINE_COLUMNS`` en
  ``data.binance_vision.normalize``).
- Un job ``fine_tune_test`` puede leer esas rutas como entradas locales (sin API
  keys) para alinear series de precio y funding en ventanas temporales comunes.
"""

from data.binance_vision.download import download_bytes
from data.binance_vision.urls import (
    funding_monthly_zip_url,
    klines_daily_zip_url,
    klines_monthly_zip_url,
)

__all__ = [
    "download_bytes",
    "funding_monthly_zip_url",
    "klines_daily_zip_url",
    "klines_monthly_zip_url",
]
