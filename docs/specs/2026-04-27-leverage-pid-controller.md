# Spec operativa: control de apalancamiento tipo PI + referencia (sin tocar el cóctel)

**Fecha:** 2026-04-27  
**Objetivo de producto:** mismo que el brief Surfer compuesto — maximizar **P(equity final ≥ 1000)** desde **140**, ruina **≤ 70**, cóctel **inalterable**.  
**Alcance de esta spec:** sustituir o coexistir con el **ladder escalonado** (`lev1/lev2/lev3` + `t1/t2`) por una política **continua + corrección PI** con límites y anti-windup, aplicada **solo** donde hoy se fija el leverage al abrir posición.

---

## 1. Invariantes (no negociables)

- Entrada/salida: misma lógica **Cóctel** (EMA200 1d, SMA200 4h, anti-whipsaw) en `sim_window` de `compound_optimize_runner.py`.
- No nuevas series de precio ni nuevas ventanas MA para señal.
- `cap`, `tgt`, `kill`, fees y funding: mismos que la corrida baseline salvo experimento documentado.
- Métricas y gates de reporting: los definidos en `docs/brainstorms/2026-04-27-surfer-compound-win-requirements.md` y `docs/ce-optimize-spec.yaml` (más walk-forward si aplica).

---

## 2. Instantes de decisión (cadencia)

**v1 (recomendada, mínimo diff respecto al código actual):** el leverage efectivo `L` solo se recalcula en los mismos instantes en que hoy se asigna `lev` al **abrir** una nueva posición tras el chequeo semanal (`i % sw == 0` con `sw = 7 * 288`).

- Mientras la posición siga abierta **sin** rotación de activo / re-señal que implique cierre y nueva apertura, **no** se re-aplica el controlador intra-semana (igual espíritu que hoy: el `lev` usado al abrir rige hasta el cierre de esa pierna).
- **v1.1 (opcional, explícitamente fuera de v1):** recalcular `L` cada barra o cada día con posición abierta y **re-sintonizar** notional (riesgo de más fees y definición de “rebalance”); no implementar salvo nuevo brief.

---

## 3. Variables de estado del controlador

Por cada ventana simulada, mantener escalares actualizados solo en instantes de decisión `k`:

| Símbolo | Significado |
|--------|-------------|
| `E_k` | Equity total **justo antes** de abrir la nueva posición (`eq_total` en el código, incl. vault si aplica). |
| `L^ff_k` | **Referencia feedforward** (ladder suavizado, solo función de `E_k`). |
| `e_k` | **Error de seguimiento** hacia meta de capital (definición dual, §4). |
| `I_k` | **Estado integral** con anti-windup (§6). |
| `u_k` | Salida PI antes de clamp: `u_k = K_p * e_k + K_i * I_k`. |
| `L_k` | Leverage entero o semi-entero **final** tras clamp y cuantización (§7). |

Condiciones iniciales: `I_0 = 0` al inicio de cada ventana (o al primer instante de decisión tras `lb`); documentar si se prefiere persistir `I` intra-ventana (no recomendado en v1).

---

## 4. Referencia feedforward `L^ff(E)` (sustituto suave del ladder)

Objetivo: misma familia que tres tramos, pero **sin saltos discontinuos** en el borde de umbrales (reduce flip-flop de política).

**Parámetros configurables:**

- `L_low`, `L_mid`, `L_high`: cotas de referencia (ej. 5, 8, 10).
- `E_a`, `E_b`: puntos de transición en USD (ej. alineados a 220 y 280 o a `t1`,`t2` actuales).
- `w_a`, `w_b` > 0: anchos de transición (logística).

**Definición normativa (logística en dos tramos):**

1. Normalizar \(x = (E - E_a) / w_a\).  
   \(s_a = 1 / (1 + \exp(-x))\) (sigmoide).  
   \(L^{(1)} = L_{\text{low}} + (L_{\text{mid}} - L_{\text{low}}) * s_a\).

2. \(x' = (E - E_b) / w_b\), \(s_b\) igual.  
   \(L^{ff} = L^{(1)} + (L_{\text{high}} - L_{\text{mid}}) * s_b\), luego **clamp** a `[L_hard_min, L_hard_max]`.

Valores por defecto sugeridos para acotar búsqueda: `L_hard_min = 3`, `L_hard_max = 12`, `w_a = w_b = 15` USD (ajustar en sweep).

---

## 5. Modo dual del error `e_k` (no usar solo “distancia a 1000”)

**Problema a evitar:** para `E` lejos de 1000 pero cerca de ruina, minimizar `log(1000) - log(E)` empuja mentalmente el control hacia **más** riesgo.

**Regla operativa:**

- Si `E_k < S_mode` (default **250** USD, configurable = misma “etapa survival” del brief):  
  **`e_k = 0`** (desactiva el término “meta 1000”). Solo aplica `L^ff(E_k)` en v1; opcional v1.0b: `e_k = K_surv * (log(E_k / E_ref) - 0)` con `E_ref = 2 * cap` y ganancia **negativa** definida en plan si se desea tirar suavemente el PI hacia conservador — **no activar sin segundo experimento** para no duplicar efecto con `L^ff`.

- Si `E_k ≥ S_mode`:  
  \[
  e_k = \log(\max(T_{\text{goal}}, \varepsilon)) - \log(\max(E_k, \varepsilon))
  \]
  con `T_goal = 1000` y `ε = 1e-6` (evitar log(0)).

Interpretación: `e_k > 0` ⇒ estás **por debajo** de la meta en escala log ⇒ el PI puede **subir** leverage respecto a la referencia (hasta clamp).

---

## 6. Ley PI y anti-windup

**Proporcional:** `u_p = K_p * e_k`.

**Integral:** antes de actualizar `I`, proponer `I_{cand} = I_k + e_k * Δt_eff` donde `Δt_eff = 1` en unidades de “paso de decisión” semanal (consistente con un solo índice `k`).

**Anti-windup (condicional simple, v1):**

1. Calcular `u_raw = K_p * e_k + K_i * I_{cand}`.
2. `L_prop = L^ff_k + u_raw`.
3. Si `L_prop > L_hard_max`: fijar `L_k = L_hard_max` y **no** actualizar integral (`I_{k+1} = I_k`) *o* usar regla de back-calculation mínima: `I_{k+1} = I_k` (documentar elección en código).
4. Análogo si `L_prop < L_hard_min`.

**Ganancias por defecto para grid inicial:** `K_p ∈ {0, 0.25, 0.5}`, `K_i ∈ {0, 0.05, 0.1}`, `I` clamp a `[-I_max, I_max]` con `I_max = 2` (unidades de error log ≈ órdenes de magnitud relativos).

**Término D:** **no** en v1 (derivada sobre equity ruidoso en pasos semanales ya es frágil).

---

## 7. Cuantización y límites duros

1. `L_float = clamp(L^ff_k + u_k, L_hard_min, L_hard_max)`.
2. **Cuantización:** `L_k = round(L_float)` o `floor`/`ceil` según convención de exchange simulada; documentar una sola convención en el runner.
3. **Mínimo absoluto:** si `L_k < 1`, forzar `1` o declarar configuración inválida (preferible rechazar en validación de config).

---

## 8. Interfaz con `compound_optimize_runner.py` (implementación futura)

- **Flag:** `--leverage-policy ladder|pi_ref` (nombre tentativo).
- **Modo `ladder`:** comportamiento actual (`--lev1` … `--t1` …).
- **Modo `pi_ref`:** leer bloque JSON/YAML de parámetros del §4–§7 desde CLI o archivo (`--leverage-pi-config path`).
- **Punto de enganche único:** reemplazar el bloque que hoy hace:

```text
if eq_total < t1_val: lev = lev_stages[0]
elif eq_total < t2_val: lev = lev_stages[1]
else: lev = lev_stages[2]
```

por `lev = compute_leverage_pi(eq_total, state, config)` solo cuando `leverage_policy == pi_ref` y en el instante de apertura definido en §2.

- El estado `I_k` debe vivir en variables locales al `sim_window` actualizadas solo al recalcular `lev`.

---

## 9. Bloque de configuración sugerido (para `ce-optimize` / JSON)

```yaml
leverage_policy: pi_ref
pi_ref:
  S_mode: 250
  T_goal: 1000
  L_ff:
    L_low: 5
    L_mid: 8
    L_high: 10
    E_a: 220
    E_b: 280
    w_a: 15
    w_b: 15
  hard:
    L_min: 3
    L_max: 12
  pi:
    K_p: 0.25
    K_i: 0.05
    I_max: 2.0
    anti_windup: conditional_freeze
```

El comando de medición sigue siendo el mismo patrón que `measurement.command` en `docs/ce-optimize-spec.yaml`, cambiando solo flags / archivo de config del bloque `pi_ref`.

---

## 10. Experimentos y tabúes

- **Tabú:** no introducir nuevos indicadores de entrada; no tocar `whip_threshold` ni períodos EMA/SMA en la misma corrida que calibra PI.
- **Baseline obligatoria:** misma seed y dataset que corrida ladder para comparar Δ métricas (idealmente **CRN** / pareado cuando exista soporte en código).
- **OOS:** mismo `--holdout-frac` y gates que el brief; el PI no sustituye walk-forward como gate.

---

## 11. Criterios de éxito / abandono

- **Éxito:** mejora estadísticamente defendible en **P(win terminal)** o en métrica condicional acordada **sin** empeorar **P(ruina)** y sin violar deltas walk-forward definidos.
- **Abandono:** si tras grid acotado el PI solo replica el ladder o empeora varianza entre políticas sin ganancia en P(win), documentar en `ce-compound` y mantener ladder como default.

---

## 12. Checklist de implementación (para `ce-plan`)

- [x] Función pura `leverage_pi_step(E, I_prev, cfg) -> (L, I_next)` en `leverage_pi.py`.
- [x] Tests unitarios: saturación en `L_max`/`L_min`, `e_k` con `E` justo por encima de `S_mode`, integral congelada bajo saturación (`tests/test_leverage_pi.py`).
- [x] Un run JSON con `leverage_policy` y `leverage_pi_config` en el output (`compound_optimize_runner.py`).
- [x] Script hermano `scripts/sweep_pi_ref.py` (rejilla `K_p`×`K_i` §6; flag `--sweep-w` para `w_a=w_b` en {12,15,18}).

**Uso rápido:** `python compound_optimize_runner.py --leverage-policy pi_ref` (defaults §9) o `--leverage-pi-config configs/pi_ref.example.json` (JSON isomorfo al bloque `pi_ref`; `--target-equity` fuerza `T_goal` en runtime).

**Barridos ejecutados (ejemplo):** `python scripts/sweep_pi_ref.py --holdout-frac 0.2` → `optimization/sweep_pi_ref_*_best.json`; misma línea con `--target-equity 500` para sprint 140→500.
