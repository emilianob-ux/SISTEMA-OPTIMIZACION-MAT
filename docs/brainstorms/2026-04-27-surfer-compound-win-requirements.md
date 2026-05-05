---
date: 2026-04-27
topic: surfer-compound-win-140-to-1000
---

# Requisitos: camino compuesto $140 ? $1000 (Surfer + cóctel fijo)

## Problem Frame

El operador quiere **maximizar la probabilidad de alcanzar USD 1000** partiendo de **USD 140**, usando la lógica ya validada por simulación (**Cóctel**: doble confirmación EMA200 diario + SMA200 4h + anti-whipsaw), sin abrir nuevas familias de señal que invite a *curve-fitting* sobre el mismo histórico (funding Binance 2019–2024).

El cuello de botella observado es el **trade-off** ruina vs win: los filtros fuertes bajan ruina y suben supervivencia, pero bajan el win directo a $1000. La hipótesis de producto es **win compuesto por etapas de riesgo** (más conservador al inicio, más agresivo solo con equity demostrada), midiendo también **probabilidades condicionales** (p. ej. llegar a $1000 condicionado a haber superado un umbral intermedio).

**Implementación en este repo (actualizado):** el motor de ventanas determinísticas y JSON para optimización vive en **`compound_optimize_runner.py`** (lee `data/candles.db` o `../BOTS TRADING/data/candles.db`). El barrido de rejilla y artefactos están en **`scripts/sweep_compound_ladder.py`** y **`optimization/sweep_*`**. La spec tipo `ce-optimize` de ejemplo: **`ce-optimize-spec.yaml`** (raíz) y **`docs/ce-optimize-spec.yaml`**.

---

## Requirements

**Objetivo y métricas**

- R1. La **meta terminal** sigue siendo **equity final ? 1000 USD** (o la unidad monetaria configurada equivalente), desde saldo inicial **140 USD**.
- R2. El backtest debe reportar como mínimo: **P(win terminal)** (estimador Monte Carlo o el definido hoy), **P(ruina)** con definición explícita acordada (p. ej. equity ? umbral de muerte), y **P(supervivencia “media”)** si se usa, con la misma definición que en tablas ya publicadas.
- R3. Añadir **métricas de camino compuesto**, al menos: **P(ruina antes de duplicar capital inicial)** (o antes de cruzar umbral de etapa 1), y **P(win terminal | equity alcanzó U en algún momento)** para **U ? {250, 400}** (valores por defecto; deben ser parámetros de config).
- R4. Mantener **señal de trading fija** en la variante “v1 de producto”: **Cóctel** (doble confirmación + anti-whipsaw). No se optimizan nuevos indicadores en la misma corrida que el ladder de riesgo.

**Comportamiento de riesgo por etapas (alcance v1)**

- R5. Definir **al menos dos bandas de equity** con políticas distintas solo en **apalancamiento y/o fracción de riesgo**, no en reglas de entrada/salida del surfer. Ejemplo normativo (ajustable por config):
  - **Etapa A:** equity &lt; **250 USD** — apalancamiento reducido (p. ej. 5× o 3×) respecto al baseline 10×.
  - **Etapa B:** equity ? **250 USD** — apalancamiento nominal (p. ej. 10×) o intermedio hasta otro umbral opcional.
- R6. Opcional v1.1 (no bloquea v1): **de-risk parcial** al cruzar umbral alto (p. ej. ?400 USD), congelando una **fracción** del equity en “efectivo” no arriesgado; la fracción y el umbral son parámetros, default puede ser **0%** (apagado) para no multiplicar superficie antes del primer experimento.

**Validación y tabúes anti–curve-fitting**

- R7. Lista explícita de **tabúes**: no añadir nuevas ventanas de MA/EMA distintas de las ya usadas en cóctel; no optimizar día de rotación salvo experimento aparte marcado como “exploratorio”.
- R8. Cualquier barrido de parámetros del ladder debe poder acompañarse de **validación temporal** (walk-forward: entrenar/barrer en ventana W, medir en ventana siguiente) como **gate de robustez** antes de declarar ganador — la métrica exacta del gate se fija en planificación (p. ej. “ruina OOS no empeora más de X pp vs IS”).
  - **Implementado (v1):** flag CLI `--holdout-frac` en `compound_optimize_runner.py`: parte **temporal final** de las ventanas deslizantes como **holdout**; el JSON incluye `walk_forward.in_sample`, `walk_forward.holdout` y deltas `delta_p_ruin_oos_minus_is` / `delta_p_win_terminal_oos_minus_is`. El sweep puede propagar `--holdout-frac` vía `scripts/sweep_compound_ladder.py`.

---

## Success Criteria

- El sistema de medición permite **comparar en una tabla** baseline (cóctel fijo, 10× todo el trayecto) vs **ladder** usando las mismas seeds y costos.
- Se observa al menos una **hipótesis cuantificada** del tipo: “sube P(win terminal)” o “sube P(win | pasó etapa 1)” **sin** violar gates de ruina acordados, o se documenta que el ladder no mejora y se abandona con evidencia.

---

## Scope Boundaries

- Fuera de alcance v1: nuevos activos, nueva lógica de funding distinta a la ya modelada, optimización libre de hiperparámetros técnicos del surfer.
- Fuera de alcance: recomendaciones de trading en vivo, compliance, ejecución en exchange.
- El repo **SISTEMA-OPTIMIZACION-MAT** ya contiene el **runner** y el **sweep**; Hydra u otros orquestadores son opcionales.

---

## Key Decisions

- **Congelar señal (cóctel), mover palanca en gestión de riesgo por equity** — maximiza claridad causal y reduce superficie de ajuste sobre precio/funding.
- **Métricas condicionales obligatorias** — sin ellas, es fácil “mejorar” ruina y no darse cuenta de que el win terminal murió en el tramo bajo.
- **Walk-forward como gate, no como único score** — evita elegir un ladder que solo funciona en 2019–2021.

---

## Dependencies / Assumptions

- Existe o existirá un comando reproducible de simulación (p. ej. `python -m hydra.backtest.fine_tune_test`) con datos **funding Binance 2019–2024** (o el set acordado).
- Las definiciones de **ruina**, **fees**, **apalancamiento** y número de trayectorias MC son las mismas entre corridas salvo lo explicitado en config del ladder.
- El operador acepta que **P(win terminal)** pueda moverse poco si el ladder prioriza **supervivencia temprana**; el éxito del proyecto se juzga por el criterio de Success Criteria arriba, no por un solo número.

---

## Decisiones cerradas (antes: Resolve Before Planning; Monte Carlo — estándar de comparación)

- **Ruina:** equity **≤ 70 USD** (fijo; todas las tablas comparables usan este umbral).
- **Trayectorias:** **mínimo 1000** por configuración; valor por defecto en `optimization/contract.json`: **1000** (si se necesita más precisión estadística, subir `n_paths` pero siempre documentar).
- **Semilla:** **42** fija.
- **Baseline vs ladder (innegociable):** en el **runner real** las **2368 ventanas** son determinísticas (mismo dataset); comparar políticas es directo. En el **surrogate** `optimization/mc_ladder.py`, baseline y rejilla comparten matriz Z tras calibración (ver notas en ese script).

### Deferred to Planning

- (Opcional) Integrar `measurement.command` con la skill **`ce-optimize`** en `.context/...` cuando se use ese flujo formal.
- Gate explícito sobre **`walk_forward.delta_p_ruin_oos_minus_is`** (umbral en pp) en el orquestador de optimización.

---

## Next Steps

1. **Barridos con OOS:** `python scripts/sweep_compound_ladder.py --preset quick --holdout-frac 0.2` (y revisar `walk_forward` en cada línea del JSONL).
2. **Elegir ganador** con doble criterio: factible en **full** `p_ruin` y estable en **holdout** (ej. delta OOS-IS acotado).
3. **(Opcional)** enganchar `ce-optimize-spec.yaml` de la raíz al pipeline `ce-optimize` para logs append-only.

Archivo complementario de ejemplo para optimización: `docs/brainstorms/surfer-compound-optimize-spec.example.yaml` (y `ce-optimize-spec.yaml` en la raíz).
