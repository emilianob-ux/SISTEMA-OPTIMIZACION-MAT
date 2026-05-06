# Tutorial: primer corrido reproducible

Guía paso a paso para tener **tests verdes** y **una salida JSON del runner** en tu máquina. Tiempo típico en laptop moderna: **1–3 minutos** (según red al instalar paquetes).

## 0. Prerrequisitos

- Python **3.11 o 3.12** (`python --version`).
- Estar en la **raíz del repositorio** (donde están `compound_optimize_runner.py` y `pyproject.toml`).

## 1. Entorno virtual (recomendado)

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

## 2. Instalar dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

Equivalente editable:

```bash
pip install -e ".[dev]"
```

## 3. Dataset sintético (SQLite local)

Genera `data/synthetic_signal_tune.db` (no sube al repo por `.gitignore` si lo movés a `data/*.db` estándar; el script usa la ruta esperada por CI):

```bash
python scripts/bootstrap_synthetic_candles_db.py
```

Si el comando termina sin traceback, el archivo debería existir para los siguientes pasos.

## 4. Tests

```bash
pytest tests/ -q
```

Salida esperada: todos los tests en verde.

## 5. Corrida del runner (JSON en stdout)

Holdout 20 % (como en el README):

```bash
python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0.2
```

Para validar rápido que el JSON es parseable:

```bash
python compound_optimize_runner.py --db data/synthetic_signal_tune.db --holdout-frac 0.2 | python -c "import json,sys; d=json.load(sys.stdin); print('OK', 'p_win_terminal' in d, 'p_ruin' in d)"
```

Deberías ver `OK True True` (o equivalente).

## 6. Siguientes pasos

- Reglas de señal en JSON: [`signal_rules_examples.md`](signal_rules_examples.md).
- Esquema de datos reales: [`DATASET.md`](DATASET.md).
- Optimización por rejilla (preset liviano):  
  `python scripts/optimize_signal_grid.py --db data/synthetic_signal_tune.db --preset smoke --skip-pairs --holdout-frac 0.2`

## Problemas frecuentes

| Síntoma | Qué revisar |
|--------|-------------|
| `No module named ...` | Activaste el venv e instalaste `requirements*.txt` o `pip install -e ".[dev]"`. |
| No existe la DB | Volvé a ejecutar `bootstrap_synthetic_candles_db.py` desde la raíz del repo. |
| Tests fallan | Python ≥ 3.11; si cambiaste código del runner, compará con la última `main` en GitHub. |
