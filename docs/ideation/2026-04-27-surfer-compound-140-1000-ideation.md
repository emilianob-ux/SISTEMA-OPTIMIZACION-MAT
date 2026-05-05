---
date: 2026-04-27
topic: surfer-compound-140-1000
focus: maximizar P(equity final >= 1000) desde 140 USD con cóctel fijo y gates de ruina/OOS
mode: repo-grounded
---

# Ideation: camino compuesto $140 → $1000

## Grounding Context

- **Forma del repo:** Python con `compound_optimize_runner.py` (ventanas determinísticas, JSON, holdout walk-forward), `scripts/sweep_compound_ladder.py`, surrogate `optimization/mc_ladder.py`, artefactos en `optimization/sweep_*`, contrato numérico en `optimization/contract.yaml` / `contract.json`, documentación SK-MATHS en `SK-MATHS/`.
- **Brief ya existente:** `docs/brainstorms/2026-04-27-surfer-compound-win-requirements.md` fija ruina a 70 USD, seed 42, n_paths ≥ 1000, cóctel congelado, ladder por equity (apalancamiento/riesgo), métricas condicionales y walk-forward como gate.
- **Spec ce-optimize:** `docs/ce-optimize-spec.yaml` — primario `p_win_terminal`, gates `p_ruin`, `n_paths`, diagnósticos condicionales y `p_ruin_before_double`.
- **Learnings (`docs/solutions/`):** no hay carpeta visible en el árbol actual; no se incorporaron apuntes institucionales adicionales desde ahí.
- **Apalancamiento:** el cuello de botella reconocido es trade-off ruina vs P(hit $1000); el producto ya apunta a *riesgo por etapas* sin tocar la señal.

## Ranked Ideas (supervivientes)

### 1. Histéresis en umbrales del ladder (evitar flip-flop de política)

**Description:** Al cruzar 250 USD (o umbral configurable), no alternar apalancamiento en cada tick que roce el umbral; exigir buffer (p. ej. subir lev solo si equity ≥ 250 + ε, bajar solo si ≤ 250 − ε) o persistencia N pasos.

**Rationale:** El dolor real de muchos ladders es la *inestabilidad de política* cerca del umbral, que introduce varianza extra en trayectorias sin interpretación económica clara.

**Downsides:** Añade 1–2 hiperparámetros (ε o N); hay que acotarlos en sweep o fijarlos normativamente para no inflar superficie.

**Confidence:** 72%

**Complexity:** Medium

**Status:** Unexplored

---

### 2. Comparación pareada baseline vs ladder (common random numbers / mismas semillas y mismos shocks)

**Description:** Garantizar que cada trayectoria MC use el mismo stream de innovaciones (o el mismo subsample de ventanas) al comparar políticas, de modo que el estimador de **ΔP(win)** y **Δp_ruin** tenga menor varianza.

**Rationale:** Con 1000 trayectorias, el ruido de estimación puede matar `ce-optimize`; el emparejamiento es palanca estadística barata si el motor lo permite.

**Downsides:** Requiere revisar `mc_ladder.py` / runner para asegurar que baseline y ladder comparten RNG estructuralmente (no solo misma seed global con ramas distintas).

**Confidence:** 78%

**Complexity:** Medium

**Status:** Unexplored

---

### 3. Optimización en dos fases: primero métricas condicionales, luego incondicional

**Description:** Fase A: maximizar o acotar **P(win | cruzó U)** y **P(ruina antes de duplicar)** bajo gates; Fase B: solo sobre candidatos que pasen A, optimizar **P(win terminal)** y walk-forward.

**Rationale:** Separa “morir en el tramo bajo” de “no cerrar el salto final a 1000”; evita confundir mejora de supervivencia con mejora de hit terminal.

**Downsides:** Más complejidad operativa en el orquestador de experimentos; hay que definir orden y no sobreajustar la fase A.

**Confidence:** 70%

**Complexity:** Medium

**Status:** Unexplored

---

### 4. Segunda palanca de riesgo: tope de notional / fracción de equity en riesgo (además de lev discreto)

**Description:** Mantener cóctel e incluso apalancamiento nominal; añadir cap de exposición como fracción del equity o notional máximo por etapa.

**Rationale:** Misma señal, distinta geometría de pérdidas; puede mover P(win) sin nuevas ventanas MA (alineado con tabúes R4/R7).

**Downsides:** Modelar bien fees/funding con caps; más parámetros si no se fijan pocos valores normativos.

**Confidence:** 65%

**Complexity:** Medium–High

**Status:** Unexplored

---

### 5. Métrica proxy de utilidad suave cerca de $1000 (búsqueda), hit duro en reporting

**Description:** Para barridos grandes, usar una métrica continua (p. ej. esperanza de min(equity_final/1000, 1) con concavidad, o log-utilidad truncada) como **objetivo de ranking interno**; seguir reportando P(equity ≥ 1000) y gates duros.

**Rationale:** Reduce varianza del “solo binario” en el loop de optimización; el gate final sigue siendo interpretable para el operador.

**Downsides:** Riesgo de desalineación si la proxy elige políticas que suben utilidad pero no el hit duro — debe comprobarse siempre contra P(win terminal).

**Confidence:** 58%

**Complexity:** Medium

**Status:** Unexplored

---

### 6. Estrés por bloques de correlación (funding / régimen) alineado con SK-MATHS

**Description:** Si el surrogate o el agregador asume independencia excesiva entre ventanas o regímenes, introducir **bootstrap por bloques** (semanas/meses) o escenarios de correlación BTC–ETH en stress, como gate adicional, no como único score.

**Rationale:** Alineación explícita con `SimulationStressTest` / robustez; reduce confianza en políticas frágiles a correlación omitida.

**Downsides:** Coste computacional y trabajo de diseño del generador de escenarios; puede ser v1.2 si v1 es ladder + OOS.

**Confidence:** 62%

**Complexity:** High

**Status:** Unexplored

---

### 7. Digest automático post-sweep (rank + gates + Δ OOS)

**Description:** Script o paso que lea JSONL de sweeps, ordene por primario, marque violaciones de gates y resuma `walk_forward` deltas; salida única para humanos y para `ce-compound`.

**Rationale:** No sube P(win) por sí solo, pero hace viable la disciplina de `ce-optimize` (muchas corridas sin perder el hilo).

**Downsides:** Mantenimiento del parser si cambia el schema JSON.

**Confidence:** 85%

**Complexity:** Low

**Status:** Unexplored

---

## Rejection Summary

| # | Idea (resumida) | Motivo del rechazo |
|---|-----------------|---------------------|
| 1 | “Subir n_paths a 5000 siempre” | Demasiado vago sin política de parada ni emparejamiento; ya cubierto parcialmente por contrato. |
| 2 | Añadir nuevas EMA/SMA al cóctel | Tabú explícito (R4/R7); mejor como experimento aparte marcado exploratorio. |
| 3 | Sustituir ladder por “siempre 10× y más trades” | Rompe el marco de producto y curve-fitting de señal. |
| 4 | Integrar Hydra ya | Ya diferido en brief; no aporta idea de trading/métrica nueva. |
| 5 | Objetivo = minimizar tiempo esperado a $1000 | Interesante pero mejor como variante de brainstorm; cambia definición de éxito frente al brief actual. |
| 6 | Recomendaciones de trading en vivo | Fuera de alcance declarado. |
| 7 | “Mejor dashboard” genérico | Bajo valor relativo frente a incertidumbre estadística del estimador. |
| 8 | Duplicado de walk-forward como gate (R8) | Ya cubierto en requisitos; no cuenta como idea nueva. |
| 9 | Cambiar umbral de ruina a 50 USD sin análisis | No anclado al contrato cerrado (70 USD); requiere decisión de producto explícita. |

---

## Refinement (2026-04-27): entrada / salida con cóctel congelado

**Restricción:** mismas reglas de señal (EMA200 1d + SMA200 4h + anti-whipsaw ya acordados); no nuevas ventanas MA. Solo *cómo* entrar/salir alrededor de esa señal.

### Supervivientes (micro-lote)

#### E1. Cooldown de reentrada post-cierre

**Description:** Tras una salida (flat), obligar a esperar N barras o N horas antes de volver a abrir aunque el cóctel vuelva a alinearse.

**Rationale:** Reduce churn en rangos; puede subir P(win) si el coste del whipsaw domina sobre el coste de perder el primer tramo de tendencia.

**Downsides:** Riesgo de perder arranques V; N debe acotarse a pocos valores o fijarse normativamente.

**Confidence:** 64% · **Complexity:** Low–Medium · **Status:** Unexplored

#### E2. Time-stop de posición (tope de duración)

**Description:** Cerrar a mercado al cumplirse T tiempo en trade (p. ej. máx días en posición), independientemente del cóctel, o solo en etapa de equity baja.

**Rationale:** Corta colas de funding negativo persistente o tendencias muertas; análogo a “stop de tiempo” en gestión de riesgo.

**Downsides:** Puede truncar winners lentos; acoplar T a etapa de equity añade superficie — documentar como experimento aparte.

**Confidence:** 60% · **Complexity:** Medium · **Status:** Unexplored

#### E3. Filtro de sesión / régimen horario (sin nuevos indicadores)

**Description:** No operar en franjas UTC con spread alto o liquidez pobre (solo calendario), manteniendo el cóctel cuando la franja está permitida.

**Rationale:** Reduce eventos de ejecución adversa modelados de forma grosera; barato de implementar como máscara booleana sobre timestamps.

**Downsides:** Si el modelo de ejecución ya es idealizado, el efecto puede ser nulo; hay que validar contra datos reales de spread si existen.

**Confidence:** 55% · **Complexity:** Low · **Status:** Unexplored

#### E4. Scale-out parcial en hitos de equity (lado salida)

**Description:** Al cruzar 250 / 400 USD de equity, cerrar fracción fija de la posición aunque el cóctel siga long; el resto sigue reglas normales de salida.

**Rationale:** Conecta “gestión de riesgo por equity” con *salida*, no solo con apalancamiento; puede mejorar trayectorias que luego revierten desde picos.

**Downsides:** Se solapa parcialmente con R6 (de-risk); hay que decidir si es la misma palanca o competidor — evitar duplicar en config.

**Confidence:** 66% · **Complexity:** Medium · **Status:** Unexplored

### Rechazos (entrada/salida)

| Id | Idea | Motivo |
|----|------|--------|
| X1 | Añadir SMA 50 / RSI / nuevo timeframe | Tabú R4/R7; solo como track “exploratorio” fuera de v1. |
| X2 | “Invertir señal” (short el cóctel long) | Cambia tesis del producto; fuera del marco actual sin nuevo brief. |
| X3 | Entrada escalonada aleatoria | No accionable ni interpretable; difícil de gatear en OOS. |
| X4 | Salida solo por trailing de nueva EMA | Requiere nueva ventana MA explícita — tabú. |

---

## Menú siguiente (post–ce-ideate)

1. **Refinar** — profundizar 1–2 supervivientes con parámetros concretos.
2. **Abrir ce-brainstorm** — fijar en el brief si alguna idea altera R5–R8 o tabúes.
3. **Guardar y cerrar** — usar este archivo como entrada a `ce-plan` / barridos.
