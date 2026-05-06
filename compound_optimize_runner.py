import argparse
import json
import os
import sqlite3

import numpy as np

from leverage_pi import (
    default_pi_ref_config,
    leverage_pi_step,
    load_pi_ref_config,
    vault_leverage_for_pi,
)

# Por defecto: <raíz del repo>/data/candles.db. Si no existe, intenta el dataset del repo hermano
# "BOTS TRADING" (misma carpeta padre que PRUEBAS DE PYTHON). Override: COMPOUND_OPT_DB o --db.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.join(_REPO_ROOT, "data", "candles.db")
_SIBLING_BOTS_DB = os.path.normpath(
    os.path.join(_REPO_ROOT, "..", "BOTS TRADING", "data", "candles.db")
)


def _resolve_default_db_path() -> str:
    if os.path.isfile(_DEFAULT_DB):
        return _DEFAULT_DB
    if os.path.isfile(_SIBLING_BOTS_DB):
        return _SIBLING_BOTS_DB
    return _DEFAULT_DB


def load_data(db_path):
    co = sqlite3.connect(db_path)
    start_ts = 1567296000000
    rb = co.execute(
        "SELECT timestamp, close FROM candles "
        "WHERE symbol='BTCUSDT' AND timestamp>=? ORDER BY timestamp",
        (start_ts,),
    ).fetchall()
    re = co.execute(
        "SELECT timestamp, close FROM candles "
        "WHERE symbol='ETHUSDT' AND timestamp>=? ORDER BY timestamp",
        (start_ts,),
    ).fetchall()
    fb = co.execute(
        "SELECT timestamp, fundingRate FROM funding "
        "WHERE symbol='BTCUSDT' AND timestamp>=? ORDER BY timestamp",
        (start_ts,),
    ).fetchall()
    fe = co.execute(
        "SELECT timestamp, fundingRate FROM funding "
        "WHERE symbol='ETHUSDT' AND timestamp>=? ORDER BY timestamp",
        (start_ts,),
    ).fetchall()
    co.close()

    ts_b = [x[0] for x in rb]
    cl_b = [x[1] for x in rb]
    _ts_e = [x[0] for x in re]
    cl_e = [x[1] for x in re]
    fund_b = {x[0]: x[1] for x in fb}
    fund_e = {x[0]: x[1] for x in fe}

    n = min(len(cl_b), len(cl_e))
    cl_b = cl_b[:n]
    cl_e = cl_e[:n]
    ts_b = ts_b[:n]

    f_cost_b = np.zeros(n)
    f_cost_e = np.zeros(n)
    for i in range(n):
        t = ts_b[i]
        if t in fund_b:
            f_cost_b[i] = fund_b[t]
        if t in fund_e:
            f_cost_e[i] = fund_e[t]

    return np.array(cl_b), np.array(cl_e), f_cost_b, f_cost_e


def ema(data, period):
    res = np.zeros(len(data))
    if len(data) < period:
        return res
    res[period - 1] = np.mean(data[:period])
    k = 2 / (period + 1)
    for i in range(period, len(data)):
        res[i] = data[i] * k + res[i - 1] * (1 - k)
    return res


def sma(data, period):
    res = np.zeros(len(data))
    if len(data) < period:
        return res
    cum = np.cumsum(np.insert(data, 0, 0))
    res[period - 1 :] = (cum[period:] - cum[:-period]) / float(period)
    return res


def calc_indicators(cl):
    n = len(cl)
    days = n // 288
    d_cl = np.array([cl[min((i + 1) * 288 - 1, n - 1)] for i in range(days)])
    ema200_d = ema(d_cl, 200)
    ema200_5m = np.zeros(n)
    for i in range(days):
        ema200_5m[i * 288 : min((i + 1) * 288, n)] = ema200_d[i]

    h4_count = n // 48
    h4_cl = np.array([cl[min((i + 1) * 48 - 1, n - 1)] for i in range(h4_count)])
    sma200_h4 = sma(h4_cl, 200)
    sma200_5m = np.zeros(n)
    for i in range(h4_count):
        sma200_5m[i * 48 : min((i + 1) * 48, n)] = sma200_h4[i]

    return ema200_5m, sma200_5m


def sim_window(
    cl_b,
    cl_e,
    fcost_b,
    fcost_e,
    ema_b,
    sma_b,
    ema_e,
    sma_e,
    lev_stages=(10, 10, 10),
    thresholds=(280, 400),
    vault_trigger=9999,
    vault_pct=0.0,
    use_airbag=False,
    cap=140.0,
    tgt=1000.0,
    kill=70.0,
    fee=0.0018,
    leverage_policy="ladder",
    pi_cfg=None,
    signal_mask_b=None,
    signal_mask_e=None,
):

    sw = 7 * 288
    lb = 14 * 288
    n = len(cl_b)

    c = cap
    vault = 0.0
    asset = None
    coins = 0
    ep = 0
    whip_threshold = 0.010

    reached_t1 = False
    reached_t2 = False
    ruin_before_t1 = False
    I_pi = 0.0

    t1_val = thresholds[0]
    t2_val = thresholds[1]
    use_pi = leverage_policy == "pi_ref" and pi_cfg is not None
    vault_lev = float(vault_leverage_for_pi(pi_cfg)) if use_pi else float(lev_stages[2])

    for i in range(lb, n):
        if coins != 0:
            cl_now = cl_b[i] if asset == "BTC" else cl_e[i]
            cost_rate = fcost_b[i] if asset == "BTC" else fcost_e[i]
            if cost_rate != 0:
                c -= (coins * cl_now) * cost_rate

            eq_active = c + coins * (cl_now - ep)
            eq_total = eq_active + vault

            if not reached_t1 and eq_total >= t1_val:
                reached_t1 = True
            if not reached_t2 and eq_total >= t2_val:
                reached_t2 = True

            if vault == 0 and eq_total >= vault_trigger and vault_pct > 0:
                amount_to_vault = eq_total * vault_pct
                if amount_to_vault > 0:
                    close_cost = (amount_to_vault * vault_lev) * fee / 2
                    c -= amount_to_vault + close_cost
                    vault += amount_to_vault
                    coins = (c * vault_lev) / cl_now
                    eq_total = c + coins * (cl_now - ep) + vault

            if eq_total <= kill or c <= 0:
                if not reached_t1:
                    ruin_before_t1 = True
                return "RUIN", max(eq_total, 0), reached_t1, reached_t2, ruin_before_t1

            if eq_total >= tgt:
                return "WIN", eq_total, reached_t1, reached_t2, ruin_before_t1

        if i % sw == 0:
            mb = (cl_b[i] - cl_b[i - lb]) / cl_b[i - lb]
            me = (cl_e[i] - cl_e[i - lb]) / cl_e[i - lb]

            diff = abs(mb - me)
            if diff < whip_threshold:
                leader = asset
            else:
                leader = "BTC" if mb >= me else "ETH"

            if leader is not None:
                valid = True
                if ema_b[i] > 0 and (cl_b[i] < ema_b[i] if leader == "BTC" else cl_e[i] < ema_e[i]):
                    valid = False
                if sma_b[i] > 0 and (cl_b[i] < sma_b[i] if leader == "BTC" else cl_e[i] < sma_e[i]):
                    valid = False

                current_eq = eq_total if coins != 0 else c + vault
                if use_airbag and i == lb + sw and current_eq < 100:
                    valid = False

                if valid and leader == "BTC" and signal_mask_b is not None:
                    if not signal_mask_b[i]:
                        valid = False
                if valid and leader == "ETH" and signal_mask_e is not None:
                    if not signal_mask_e[i]:
                        valid = False

                if not valid:
                    leader = None

            if leader != asset:
                if coins != 0:
                    cl_now = cl_b[i] if asset == "BTC" else cl_e[i]
                    pnl = coins * (cl_now - ep)
                    cost = abs(coins) * cl_now * fee / 2
                    c += pnl - cost
                    coins = 0

                eq_total = c + vault
                if not reached_t1 and eq_total >= t1_val:
                    reached_t1 = True
                if not reached_t2 and eq_total >= t2_val:
                    reached_t2 = True

                if vault == 0 and eq_total >= vault_trigger and vault_pct > 0:
                    amount_to_vault = eq_total * vault_pct
                    c -= amount_to_vault
                    vault += amount_to_vault
                    eq_total = c + vault

                if eq_total <= kill:
                    if not reached_t1:
                        ruin_before_t1 = True
                    return "RUIN", eq_total, reached_t1, reached_t2, ruin_before_t1
                if eq_total >= tgt:
                    return "WIN", eq_total, reached_t1, reached_t2, ruin_before_t1

                if leader is not None:
                    if use_pi:
                        lev, I_pi = leverage_pi_step(eq_total, I_pi, pi_cfg)
                    else:
                        if eq_total < t1_val:
                            lev = lev_stages[0]
                        elif eq_total < t2_val:
                            lev = lev_stages[1]
                        else:
                            lev = lev_stages[2]

                    price = cl_b[i] if leader == "BTC" else cl_e[i]
                    pv = c * lev
                    coins = pv / price
                    ep = price
                    asset = leader
                    c -= pv * fee / 2
                else:
                    asset = None

    if coins != 0:
        cl_now = cl_b[-1] if asset == "BTC" else cl_e[-1]
        c += coins * (cl_now - ep) - abs(coins) * cl_now * fee / 2

    eq_total = c + vault
    return "SURV", eq_total, reached_t1, reached_t2, ruin_before_t1


def metrics_over_windows(
    *,
    cl_b,
    cl_e,
    fcost_b,
    fcost_e,
    ema_b,
    sma_b,
    ema_e,
    sma_e,
    w: int,
    step: int,
    ww_start: int,
    ww_end: int,
    lev1: float,
    lev2: float,
    lev3: float,
    t1: float,
    t2: float,
    derisk: float,
    use_airbag: bool,
    cap: float,
    tgt: float,
    kill: float,
    leverage_policy: str = "ladder",
    pi_cfg=None,
    signal_mask_b=None,
    signal_mask_e=None,
) -> dict:
    """Agrega métricas sobre ventanas ww en [ww_start, ww_end) (índices de ventana deslizante)."""
    wi = ru = su = 0
    ruin_b_t1_cnt = 0
    reached_t1_cnt = 0
    reached_t2_cnt = 0
    win_given_t1_cnt = 0
    win_given_t2_cnt = 0
    n_paths = max(0, ww_end - ww_start)
    if n_paths == 0:
        return {
            "p_win_terminal": 0.0,
            "p_ruin": 0.0,
            "p_survive_medium": 0.0,
            "p_ruin_before_double": 0.0,
            "p_win_given_crossed_250": 0.0,
            "p_win_given_crossed_400": 0.0,
            "n_paths": 0,
        }

    for ww in range(ww_start, ww_end):
        s = ww * step
        e = s + w
        smb = signal_mask_b[s:e] if signal_mask_b is not None else None
        sme = signal_mask_e[s:e] if signal_mask_e is not None else None
        res, _final_eq, reached_t1, reached_t2, ruin_before_t1 = sim_window(
            cl_b[s:e],
            cl_e[s:e],
            fcost_b[s:e],
            fcost_e[s:e],
            ema_b[s:e],
            sma_b[s:e],
            ema_e[s:e],
            sma_e[s:e],
            lev_stages=(lev1, lev2, lev3),
            thresholds=(t1, t2),
            vault_trigger=t2,
            vault_pct=derisk,
            use_airbag=use_airbag,
            cap=cap,
            tgt=tgt,
            kill=kill,
            leverage_policy=leverage_policy,
            pi_cfg=pi_cfg,
            signal_mask_b=smb,
            signal_mask_e=sme,
        )

        if reached_t1:
            reached_t1_cnt += 1
        if reached_t2:
            reached_t2_cnt += 1
        if ruin_before_t1:
            ruin_b_t1_cnt += 1

        if res == "WIN":
            wi += 1
            if reached_t1:
                win_given_t1_cnt += 1
            if reached_t2:
                win_given_t2_cnt += 1
        elif res == "RUIN":
            ru += 1
        else:
            su += 1

    nw = n_paths
    p_win_given_crossed_t1 = (win_given_t1_cnt / reached_t1_cnt) if reached_t1_cnt > 0 else 0.0
    p_win_given_crossed_t2 = (win_given_t2_cnt / reached_t2_cnt) if reached_t2_cnt > 0 else 0.0
    return {
        "p_win_terminal": wi / nw,
        "p_ruin": ru / nw,
        "p_survive_medium": su / nw,
        "p_ruin_before_double": ruin_b_t1_cnt / nw,
        "p_win_given_crossed_250": p_win_given_crossed_t1,
        "p_win_given_crossed_400": p_win_given_crossed_t2,
        "n_paths": nw,
    }


def main():
    parser = argparse.ArgumentParser(description="Compound Win optimizer runner (JSON a stdout)")
    parser.add_argument(
        "--db",
        type=str,
        default=os.environ.get("COMPOUND_OPT_DB") or _resolve_default_db_path(),
        help=(
            "SQLite con tablas candles y funding (BTCUSDT/ETHUSDT). "
            "Por defecto data/candles.db o ../BOTS TRADING/data/candles.db"
        ),
    )
    parser.add_argument("--lev1", type=float, default=10, help="Leverage para etapa 1")
    parser.add_argument("--lev2", type=float, default=10, help="Leverage para etapa 2")
    parser.add_argument("--lev3", type=float, default=10, help="Leverage para etapa 3")
    parser.add_argument("--t1", type=float, default=280, help="Umbral de eq para etapa 2")
    parser.add_argument("--t2", type=float, default=400, help="Umbral de eq para etapa 3")
    parser.add_argument(
        "--derisk", type=float, default=0.0, help="Fracción a congelar al cruzar t2"
    )
    parser.add_argument(
        "--early-airbag", type=str, default="false", help="Airbag semana 1 (true/false)"
    )
    parser.add_argument(
        "--holdout-frac",
        type=float,
        default=0.0,
        help=(
            "Fraccion temporal OOS al final de las ventanas (0=desactivado). "
            "R8 walk-forward liviano."
        ),
    )
    parser.add_argument(
        "--target-equity",
        type=float,
        default=1000.0,
        help="Meta de equity (WIN si eq_total >= este valor). Ej. 500 para sprint 140->500.",
    )
    parser.add_argument(
        "--start-capital",
        type=float,
        default=140.0,
        help="Capital inicial USD por ventana.",
    )
    parser.add_argument(
        "--kill-equity",
        type=float,
        default=70.0,
        help="Umbral de ruina (equity <= kill).",
    )
    parser.add_argument(
        "--leverage-policy",
        type=str,
        choices=("ladder", "pi_ref"),
        default="ladder",
        help=(
            "ladder: lev1/lev2/lev3 + t1/t2. pi_ref: PI + L^ff "
            "(spec docs/specs/2026-04-27-leverage-pid-controller.md)."
        ),
    )
    parser.add_argument(
        "--leverage-pi-config",
        type=str,
        default="",
        help="Ruta JSON con bloque pi_ref (opcional; si pi_ref y vacío, defaults de la spec).",
    )
    parser.add_argument(
        "--signal-config",
        type=str,
        default="",
        help=(
            "JSON v1 de reglas extra (EMA/ADX/ATR/Boll/volumen). Ver docs/signal_rules_examples.md"
        ),
    )

    args = parser.parse_args()

    use_airbag = args.early_airbag.lower() == "true"

    # Los "1000 trayectorias" son en nuestro caso las 2368 ventanas determinísticas
    # de datos históricos reales (walk-forward overlapping), equivalente a semillas estáticas.

    db_path = os.path.abspath(args.db)
    if not os.path.isfile(db_path):
        err = {
            "error": "db_not_found",
            "path": db_path,
            "hint": (
                "Coloca candles.db en data/, define COMPOUND_OPT_DB, "
                "o usa el dataset en ../BOTS TRADING/data/candles.db "
                "(misma carpeta PRUEBAS DE PYTHON)."
            ),
        }
        print(json.dumps(err))
        raise SystemExit(2)

    cl_b, cl_e, fcost_b, fcost_e = load_data(db_path)
    ema_b, sma_b = calc_indicators(cl_b)
    ema_e, sma_e = calc_indicators(cl_e)

    signal_mask_b = None
    signal_mask_e = None
    sig_path = (args.signal_config or "").strip()
    if sig_path:
        from features.loaders import load_btc_eth_series
        from features.signal_rules import load_signal_config, masks_from_ohlcv

        cfg_sig = load_signal_config(os.path.abspath(sig_path))
        _clb, _cle, hi_b, lo_b, vo_b, hi_e, lo_e, vo_e = load_btc_eth_series(db_path)
        n0 = len(cl_b)
        if len(_clb) < n0 or len(_cle) < n0:
            err = {
                "error": "signal_ohlcv_shorter_than_close",
                "len_close": n0,
                "len_ohlcv_b": len(_clb),
                "hint": "Verifica que candles tenga la misma longitud para BTC/ETH.",
            }
            print(json.dumps(err))
            raise SystemExit(2)
        hi_b = hi_b[:n0] if hi_b is not None else None
        lo_b = lo_b[:n0] if lo_b is not None else None
        vo_b = vo_b[:n0] if vo_b is not None else None
        hi_e = hi_e[:n0] if hi_e is not None else None
        lo_e = lo_e[:n0] if lo_e is not None else None
        vo_e = vo_e[:n0] if vo_e is not None else None
        signal_mask_b = masks_from_ohlcv(cl_b, hi_b, lo_b, vo_b, cfg_sig)
        signal_mask_e = masks_from_ohlcv(cl_e, hi_e, lo_e, vo_e, cfg_sig)

    n = len(cl_b)
    w = 17280
    step = 288
    nw = (n - w) // step + 1
    bars_per_day = 288
    window_days = float(w) / float(bars_per_day)

    hf = float(args.holdout_frac or 0.0)
    if hf < 0 or hf >= 0.95:
        err = {
            "error": "invalid_holdout_frac",
            "holdout_frac": hf,
            "hint": "Usar 0 < holdout_frac < 0.95",
        }
        print(json.dumps(err))
        raise SystemExit(2)

    cap = float(args.start_capital)
    tgt = float(args.target_equity)
    kill = float(args.kill_equity)
    if tgt <= cap or kill >= cap:
        err = {
            "error": "invalid_cap_target_kill",
            "start_capital": cap,
            "target_equity": tgt,
            "kill_equity": kill,
        }
        print(json.dumps(err))
        raise SystemExit(2)

    leverage_policy = args.leverage_policy.strip()
    pi_cfg = None
    if leverage_policy == "pi_ref":
        path = (args.leverage_pi_config or "").strip()
        if path:
            pi_cfg = load_pi_ref_config(path, t_goal_override=tgt)
        else:
            pi_cfg = default_pi_ref_config(t_goal=tgt)
            pi_cfg["T_goal"] = float(tgt)

    results = metrics_over_windows(
        cl_b=cl_b,
        cl_e=cl_e,
        fcost_b=fcost_b,
        fcost_e=fcost_e,
        ema_b=ema_b,
        sma_b=sma_b,
        ema_e=ema_e,
        sma_e=sma_e,
        w=w,
        step=step,
        ww_start=0,
        ww_end=nw,
        lev1=args.lev1,
        lev2=args.lev2,
        lev3=args.lev3,
        t1=args.t1,
        t2=args.t2,
        derisk=args.derisk,
        use_airbag=use_airbag,
        cap=cap,
        tgt=tgt,
        kill=kill,
        leverage_policy=leverage_policy,
        pi_cfg=pi_cfg,
        signal_mask_b=signal_mask_b,
        signal_mask_e=signal_mask_e,
    )
    results["leverage_policy"] = leverage_policy
    if leverage_policy == "pi_ref" and pi_cfg is not None:
        results["leverage_pi_config"] = pi_cfg
    results["start_capital_usd"] = cap
    results["target_equity_usd"] = tgt
    results["kill_equity_usd"] = kill
    results["window_5m_bars"] = w
    results["window_calendar_days_approx"] = round(window_days, 3)
    if sig_path:
        results["signal_config_path"] = os.path.abspath(sig_path)

    if hf > 0.0:
        split = int(nw * (1.0 - hf))
        if split <= 0 or split >= nw:
            err = {
                "error": "holdout_split_degenerate",
                "nw": nw,
                "split": split,
                "holdout_frac": hf,
            }
            print(json.dumps(err))
            raise SystemExit(2)
        in_sample = metrics_over_windows(
            cl_b=cl_b,
            cl_e=cl_e,
            fcost_b=fcost_b,
            fcost_e=fcost_e,
            ema_b=ema_b,
            sma_b=sma_b,
            ema_e=ema_e,
            sma_e=sma_e,
            w=w,
            step=step,
            ww_start=0,
            ww_end=split,
            lev1=args.lev1,
            lev2=args.lev2,
            lev3=args.lev3,
            t1=args.t1,
            t2=args.t2,
            derisk=args.derisk,
            use_airbag=use_airbag,
            cap=cap,
            tgt=tgt,
            kill=kill,
            leverage_policy=leverage_policy,
            pi_cfg=pi_cfg,
            signal_mask_b=signal_mask_b,
            signal_mask_e=signal_mask_e,
        )
        holdout = metrics_over_windows(
            cl_b=cl_b,
            cl_e=cl_e,
            fcost_b=fcost_b,
            fcost_e=fcost_e,
            ema_b=ema_b,
            sma_b=sma_b,
            ema_e=ema_e,
            sma_e=sma_e,
            w=w,
            step=step,
            ww_start=split,
            ww_end=nw,
            lev1=args.lev1,
            lev2=args.lev2,
            lev3=args.lev3,
            t1=args.t1,
            t2=args.t2,
            derisk=args.derisk,
            use_airbag=use_airbag,
            cap=cap,
            tgt=tgt,
            kill=kill,
            leverage_policy=leverage_policy,
            pi_cfg=pi_cfg,
            signal_mask_b=signal_mask_b,
            signal_mask_e=signal_mask_e,
        )
        results["walk_forward"] = {
            "holdout_frac": hf,
            "split_first_oos_window_index": split,
            "in_sample": in_sample,
            "holdout": holdout,
            "delta_p_ruin_oos_minus_is": holdout["p_ruin"] - in_sample["p_ruin"],
            "delta_p_win_terminal_oos_minus_is": holdout["p_win_terminal"]
            - in_sample["p_win_terminal"],
        }

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
