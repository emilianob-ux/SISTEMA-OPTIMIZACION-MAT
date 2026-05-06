"""
Optimización por rejilla acotada de reglas --signal-config (cóctel fijo + filtros).

Criterios por defecto (ajustables por CLI):
  - Maximizar P(win terminal) en **holdout** temporal si --holdout-frac > 0.
  - Gates: p_ruin global y holdout <= --p-ruin-max; |delta_p_ruin OOS-IS| <= --max-delta-ruin.

Fases:
  1) Baseline sin --signal-config.
  2) Reglas simples (un solo filtro).
  3) Pares (AND) entre los mejores singles que pasaron gates.

Salida: JSON en optimization/ (ruta configurable).

Uso:
  python scripts/optimize_signal_grid.py --db data/candles.db
  python scripts/optimize_signal_grid.py  # COMPOUND_OPT_DB / data/candles.db / hermano BOTS TRADING
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _ROOT / "compound_optimize_runner.py"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _resolve_db(cli_db: str | None) -> str | None:
    if cli_db:
        p = Path(cli_db).resolve()
        return str(p) if p.is_file() else None
    env = os.environ.get("COMPOUND_OPT_DB")
    if env and Path(env).is_file():
        return str(Path(env).resolve())
    for cand in (
        _ROOT / "data" / "candles.db",
        _ROOT.parent / "BOTS TRADING" / "data" / "candles.db",
    ):
        if cand.is_file():
            return str(cand.resolve())
    return None


def _cfg_key(cfg: dict[str, Any] | None) -> str:
    if cfg is None:
        return "__baseline__"
    return json.dumps(cfg, sort_keys=True)


def _run_runner(
    db: str,
    holdout_frac: float,
    signal_cfg: dict[str, Any] | None,
    extra_runner_args: list[str],
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(_RUNNER),
        "--db",
        db,
        "--holdout-frac",
        str(holdout_frac),
        *extra_runner_args,
    ]
    tmp_path = None
    try:
        if signal_cfg is not None:
            fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="sig_", text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(signal_cfg, f)
            cmd.extend(["--signal-config", tmp_path])
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
            timeout=600,
        )
        if proc.returncode != 0:
            return {"error": "runner_failed", "stderr": (proc.stderr or "")[-2000:], "cmd": cmd}
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except json.JSONDecodeError as e:
        return {"error": "bad_json", "detail": str(e), "stdout_head": (proc.stdout or "")[:800]}
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _score_row(
    out: dict[str, Any],
    holdout_frac: float,
    p_ruin_max: float,
    max_delta_ruin: float,
) -> tuple[bool, float, str]:
    """
    Devuelve (feasible, sort_key, reason_if_infeasible).
    sort_key mayor es mejor.
    """
    if "error" in out:
        return False, -1e9, out.get("error", "error")

    pr = float(out.get("p_ruin", 1.0))
    pw = float(out.get("p_win_terminal", 0.0))

    if holdout_frac <= 0.0:
        if pr > p_ruin_max:
            return False, -1e9, f"p_ruin={pr:.4f}>{p_ruin_max}"
        return True, pw, ""

    wf = out.get("walk_forward") or {}
    ho = wf.get("holdout") or {}
    is_ = wf.get("in_sample") or {}
    pr_ho = float(ho.get("p_ruin", 1.0))
    pr_is = float(is_.get("p_ruin", 1.0))
    d_ruin = float(wf.get("delta_p_ruin_oos_minus_is", pr_ho - pr_is))
    pw_ho = float(ho.get("p_win_terminal", 0.0))
    pw_is = float(is_.get("p_win_terminal", 0.0))

    if pr > p_ruin_max:
        return False, -1e9, f"global_p_ruin={pr:.4f}"
    if pr_ho > p_ruin_max:
        return False, -1e9, f"holdout_p_ruin={pr_ho:.4f}"
    if abs(d_ruin) > max_delta_ruin:
        return False, -1e9, f"|delta_p_ruin|={abs(d_ruin):.4f}>{max_delta_ruin}"

    # Priorizar holdout win; desempate: IS win y ruina OOS baja
    key = pw_ho * 10.0 + pw_is * 1.0 - abs(d_ruin) * 0.5
    return True, key, ""


def _build_singles_full() -> list[tuple[str, dict[str, Any]]]:
    """Rejilla completa (~40 singles)."""
    out: list[tuple[str, dict[str, Any]]] = []
    V = {"version": 1, "logic": "all"}

    for thr in (14, 18, 22, 26):
        out.append(
            (
                f"adx_ge_{thr}",
                {**V, "rules": [{"op": "adx_ge", "value": float(thr)}]},
            )
        )

    for p in (20, 50, 100, 200):
        for v in (-0.025, -0.01, 0.0, 0.01, 0.025):
            out.append(
                (
                    f"dist_ema{p}_ge_{v}",
                    {
                        **V,
                        "rules": [
                            {"op": "dist_close_ema_ge", "ema_period": p, "value_pct": float(v)}
                        ],
                    },
                )
            )

    for w in (0.045, 0.06, 0.075, 0.09):
        out.append(
            (
                f"bb_width_le_{w}",
                {**V, "rules": [{"op": "bb_width_le", "value": float(w)}]},
            )
        )

    for a in (0.008, 0.012, 0.016, 0.02):
        out.append(
            (
                f"atr_pct_ge_{a}",
                {**V, "rules": [{"op": "atr_pct_ge", "value": float(a)}]},
            )
        )

    for fast, slow in ((10, 50), (10, 100), (20, 100), (20, 200), (50, 200)):
        out.append(
            (
                f"ema_cross_{fast}_{slow}",
                {**V, "rules": [{"op": "ema_cross_above", "fast": fast, "slow": slow}]},
            )
        )

    for vr in (0.1, 0.25, 0.5):
        out.append(
            (
                f"vol_ratio_ge_{vr}",
                {**V, "rules": [{"op": "vol_ratio_ge", "value": float(vr)}]},
            )
        )

    return out


def _build_singles_smoke() -> list[tuple[str, dict[str, Any]]]:
    """Rejilla pequeña para DB corta o smoke tests."""
    out: list[tuple[str, dict[str, Any]]] = []
    V = {"version": 1, "logic": "all"}
    for thr in (16, 20, 24):
        out.append((f"adx_ge_{thr}", {**V, "rules": [{"op": "adx_ge", "value": float(thr)}]}))
    for p in (20, 50, 200):
        for v in (-0.02, 0.0, 0.02):
            out.append(
                (
                    f"dist_ema{p}_ge_{v}",
                    {
                        **V,
                        "rules": [
                            {"op": "dist_close_ema_ge", "ema_period": p, "value_pct": float(v)}
                        ],
                    },
                )
            )
    for w in (0.055, 0.07, 0.09):
        out.append((f"bb_width_le_{w}", {**V, "rules": [{"op": "bb_width_le", "value": float(w)}]}))
    for a in (0.01, 0.016):
        out.append((f"atr_pct_ge_{a}", {**V, "rules": [{"op": "atr_pct_ge", "value": float(a)}]}))
    for fast, slow in ((20, 100), (50, 200)):
        out.append(
            (
                f"ema_cross_{fast}_{slow}",
                {**V, "rules": [{"op": "ema_cross_above", "fast": fast, "slow": slow}]},
            )
        )
    out.append(("vol_ratio_ge_0.2", {**V, "rules": [{"op": "vol_ratio_ge", "value": 0.2}]}))
    return out


def _build_singles(preset: str) -> list[tuple[str, dict[str, Any]]]:
    if preset == "smoke":
        return _build_singles_smoke()
    return _build_singles_full()


def _parse_runner_extra(extra: list[str]) -> dict[str, Any]:
    """Parsea --lev1 8 ... en dict para in-process."""
    d: dict[str, Any] = {}
    i = 0
    while i < len(extra):
        a = extra[i]
        if a in (
            "--lev1",
            "--lev2",
            "--lev3",
            "--t1",
            "--t2",
            "--derisk",
            "--target-equity",
            "--start-capital",
            "--kill-equity",
        ):
            if i + 1 >= len(extra):
                break
            key = a[2:].replace("-", "_")
            if key == "target_equity":
                d["tgt"] = float(extra[i + 1])
            elif key == "start_capital":
                d["cap"] = float(extra[i + 1])
            elif key == "kill_equity":
                d["kill"] = float(extra[i + 1])
            else:
                d[key] = float(extra[i + 1])
            i += 2
            continue
        if a == "--early-airbag" and i + 1 < len(extra):
            d["use_airbag"] = str(extra[i + 1]).lower() == "true"
            i += 2
            continue
        i += 1
    return d


def _default_risk() -> dict[str, Any]:
    return {
        "lev1": 10.0,
        "lev2": 10.0,
        "lev3": 10.0,
        "t1": 280.0,
        "t2": 400.0,
        "derisk": 0.0,
        "use_airbag": False,
        "cap": 140.0,
        "tgt": 1000.0,
        "kill": 70.0,
        "leverage_policy": "ladder",
        "pi_cfg": None,
    }


def load_in_process_bundle(db: str) -> dict[str, Any] | None:
    """Carga datos una sola vez para evaluar muchas máscaras sin releer SQLite."""
    from compound_optimize_runner import calc_indicators, load_data
    from features.loaders import load_btc_eth_series
    from features.signal_rules import masks_from_ohlcv

    cl_b, cl_e, fcost_b, fcost_e = load_data(db)
    ema_b, sma_b = calc_indicators(cl_b)
    ema_e, sma_e = calc_indicators(cl_e)
    n = len(cl_b)
    w = 17280
    step = 288
    nw = (n - w) // step + 1
    if nw <= 0:
        return None
    _, _, hi_b, lo_b, vo_b, hi_e, lo_e, vo_e = load_btc_eth_series(db)
    hi_b = hi_b[:n] if hi_b is not None else None
    lo_b = lo_b[:n] if lo_b is not None else None
    vo_b = vo_b[:n] if vo_b is not None else None
    hi_e = hi_e[:n] if hi_e is not None else None
    lo_e = lo_e[:n] if lo_e is not None else None
    vo_e = vo_e[:n] if vo_e is not None else None

    def masks_for(cfg: dict[str, Any] | None) -> tuple[Any, Any]:
        if cfg is None:
            return None, None
        mb = masks_from_ohlcv(cl_b, hi_b, lo_b, vo_b, cfg)
        me = masks_from_ohlcv(cl_e, hi_e, lo_e, vo_e, cfg)
        return mb, me

    return {
        "cl_b": cl_b,
        "cl_e": cl_e,
        "fcost_b": fcost_b,
        "fcost_e": fcost_e,
        "ema_b": ema_b,
        "sma_b": sma_b,
        "ema_e": ema_e,
        "sma_e": sma_e,
        "w": w,
        "step": step,
        "nw": nw,
        "masks_for": masks_for,
    }


def in_process_metrics_from_bundle(
    bundle: dict[str, Any],
    holdout: float,
    cfg: dict[str, Any] | None,
    risk: dict[str, Any],
) -> dict[str, Any]:
    from compound_optimize_runner import metrics_over_windows

    nw = int(bundle["nw"])
    w = int(bundle["w"])
    step = int(bundle["step"])
    mask_b, mask_e = bundle["masks_for"](cfg)

    kw = dict(
        cl_b=bundle["cl_b"],
        cl_e=bundle["cl_e"],
        fcost_b=bundle["fcost_b"],
        fcost_e=bundle["fcost_e"],
        ema_b=bundle["ema_b"],
        sma_b=bundle["sma_b"],
        ema_e=bundle["ema_e"],
        sma_e=bundle["sma_e"],
        w=w,
        step=step,
        lev1=float(risk["lev1"]),
        lev2=float(risk["lev2"]),
        lev3=float(risk["lev3"]),
        t1=float(risk["t1"]),
        t2=float(risk["t2"]),
        derisk=float(risk["derisk"]),
        use_airbag=bool(risk["use_airbag"]),
        cap=float(risk["cap"]),
        tgt=float(risk["tgt"]),
        kill=float(risk["kill"]),
        leverage_policy=str(risk.get("leverage_policy", "ladder")),
        pi_cfg=risk.get("pi_cfg"),
        signal_mask_b=mask_b,
        signal_mask_e=mask_e,
    )

    m_all = metrics_over_windows(**kw, ww_start=0, ww_end=nw)
    out = dict(m_all)
    if holdout <= 0.0:
        return out
    split = int(nw * (1.0 - holdout))
    if split <= 0 or split >= nw:
        return {"error": "holdout_split_degenerate", "nw": int(nw), "split": int(split)}
    m_is = metrics_over_windows(**kw, ww_start=0, ww_end=split)
    m_ho = metrics_over_windows(**kw, ww_start=split, ww_end=nw)
    out["walk_forward"] = {
        "holdout_frac": holdout,
        "split_first_oos_window_index": split,
        "in_sample": m_is,
        "holdout": m_ho,
        "delta_p_ruin_oos_minus_is": float(m_ho["p_ruin"] - m_is["p_ruin"]),
        "delta_p_win_terminal_oos_minus_is": float(m_ho["p_win_terminal"] - m_is["p_win_terminal"]),
    }
    return out


def _merge_rules(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ra = [dict(r) for r in a["rules"]]
    rb = [dict(r) for r in b["rules"]]
    return {"version": 1, "logic": "all", "rules": ra + rb}


def _write_markdown_table(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Resultados optimización de señales",
        "",
        "| # | Config | Factible | p_win | p_ruin | p_win HO | p_ruin HO | "
        "Δruin OOS−IS | sort_key |",
        "|---|--------|------------|-------|--------|----------|-----------|--------------|----------|",
    ]
    rows = list(payload.get("all_results", []))
    rows.sort(key=lambda r: (not r.get("feasible", False), -float(r.get("sort_key", -1e9))))

    def mget(m: dict[str, Any], k: str, d: str = "") -> str:
        if not isinstance(m, dict) or "error" in m:
            return d
        v = m.get(k)
        return f"{v:.4f}" if isinstance(v, (int, float)) else d

    for idx, r in enumerate(rows, 1):
        m = r.get("metrics") or {}
        wf = m.get("walk_forward") if isinstance(m, dict) else None
        ho = (wf or {}).get("holdout") or {}
        d_ruin = (wf or {}).get("delta_p_ruin_oos_minus_is", "")
        if isinstance(d_ruin, (int, float)):
            d_ruin_s = f"{float(d_ruin):.4f}"
        else:
            d_ruin_s = ""
        lines.append(
            "| {idx} | {lab} | {fe} | {pw} | {pr} | {pwh} | {prh} | {dr} | {sk} |".format(
                idx=idx,
                lab=str(r.get("label", "")).replace("|", "\\|"),
                fe="sí" if r.get("feasible") else "no",
                pw=mget(m, "p_win_terminal", "—"),
                pr=mget(m, "p_ruin", "—"),
                pwh=mget(ho, "p_win_terminal", "—") if wf else "—",
                prh=mget(ho, "p_ruin", "—") if wf else "—",
                dr=d_ruin_s if wf else "—",
                sk=f"{float(r.get('sort_key', 0)):.4f}"
                if r.get("feasible")
                else str(r.get("gate_reason", ""))[:24],
            )
        )
    lines.append("")
    lines.append(
        "**Nota:** HO = holdout temporal (última fracción temporal). Ver `meta.db` en el JSON."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _maybe_bootstrap() -> None:
    boot = _ROOT / "scripts" / "bootstrap_synthetic_candles_db.py"
    subprocess.run([sys.executable, str(boot)], cwd=str(_ROOT), check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="", help="SQLite candles; vacío = autodetección")
    ap.add_argument("--holdout-frac", type=float, default=0.2)
    ap.add_argument(
        "--p-ruin-max", type=float, default=0.58, help="Máximo p_ruin (global y holdout)."
    )
    ap.add_argument("--max-delta-ruin", type=float, default=0.12, help="Máx |delta p_ruin OOS-IS|.")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--skip-pairs", action="store_true", help="Solo baseline + singles.")
    ap.add_argument("--max-pairs", type=int, default=36, help="Tope de combinaciones pareadas.")
    ap.add_argument(
        "--out", default="", help="JSON salida; vacío = optimization/signal_grid_<ts>.json"
    )
    ap.add_argument(
        "--preset",
        choices=("full", "smoke"),
        default="full",
        help="smoke: rejilla pequeña (~20 singles). full: rejilla amplia.",
    )
    ap.add_argument(
        "--in-process",
        dest="in_process",
        action="store_true",
        help="Evaluar en el mismo proceso (rápido; recomendado).",
    )
    ap.add_argument(
        "--subprocess",
        dest="in_process",
        action="store_false",
        help="Lanzar compound_optimize_runner.py por cada config (aislado, más lento).",
    )
    ap.set_defaults(in_process=True)
    ap.add_argument(
        "--allow-bootstrap",
        action="store_true",
        help="Si no hay DB, genera data/synthetic_signal_tune.db y continúa.",
    )
    ap.add_argument(
        "runner_extra",
        nargs="*",
        default=[],
        help="Args extra al runner después de --holdout-frac, ej. --lev1 8 --t1 250",
    )
    args = ap.parse_args()

    db = _resolve_db(args.db or None)
    if not db and args.allow_bootstrap:
        _maybe_bootstrap()
        db = str((_ROOT / "data" / "synthetic_signal_tune.db").resolve())
        if not Path(db).is_file():
            db = None
    if not db:
        print(
            json.dumps(
                {
                    "error": "db_not_found",
                    "hint": (
                        "Pasa --db, --allow-bootstrap, o define COMPOUND_OPT_DB / data/candles.db"
                    ),
                },
                indent=2,
            )
        )
        sys.exit(2)

    holdout = float(args.holdout_frac)
    extra = list(args.runner_extra)
    if "--holdout-frac" in extra:
        print(json.dumps({"error": "no_dupliques_holdout_en_runner_extra"}, indent=2))
        sys.exit(2)

    risk = {**_default_risk(), **_parse_runner_extra(extra)}

    singles = _build_singles(args.preset)
    seen: set[str] = set()
    jobs: list[tuple[str, dict[str, Any] | None]] = [("baseline", None)]
    for lab, cfg in singles:
        k = _cfg_key(cfg)
        if k in seen:
            continue
        seen.add(k)
        jobs.append((lab, cfg))

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = Path(args.out) if args.out else _ROOT / "optimization" / f"signal_grid_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

    bundle = None
    if args.in_process:
        bundle = load_in_process_bundle(db)
        if bundle is None:
            print(json.dumps({"error": "insufficient_bars", "db": db}, indent=2))
            sys.exit(2)

    def one_job(item: tuple[str, dict[str, Any] | None]) -> dict[str, Any]:
        lab, cfg = item
        if args.in_process and bundle is not None:
            raw = in_process_metrics_from_bundle(bundle, holdout, cfg, risk)
        else:
            raw = _run_runner(db, holdout, cfg, extra)
        feas, key, why = _score_row(raw, holdout, args.p_ruin_max, args.max_delta_ruin)
        return {
            "label": lab,
            "config": cfg,
            "feasible": feas,
            "sort_key": key,
            "gate_reason": why,
            "metrics": raw,
        }

    print(
        f"DB={db} jobs={len(jobs)} workers={args.workers} "
        f"in_process={args.in_process} preset={args.preset}",
        file=sys.stderr,
    )
    if args.in_process:
        results = []
        for j in jobs:
            results.append(one_job(j))
            print(f"OK {j[0]}", file=sys.stderr, flush=True)
    else:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futs = [ex.submit(one_job, j) for j in jobs]
            for fut in as_completed(futs):
                results.append(fut.result())

    # Mejor singles factibles para fase pares
    feas_s = [r for r in results if r["label"] != "baseline" and r.get("feasible")]
    feas_s.sort(key=lambda r: -r["sort_key"])
    top = feas_s[:6]
    if len(top) < 2:
        alt = sorted(
            [r for r in results if r["label"] != "baseline"],
            key=lambda r: float((r.get("metrics") or {}).get("p_win_terminal", -1.0) or -1.0),
            reverse=True,
        )[:6]
        top = alt if len(alt) >= 2 else top
    pair_jobs: list[tuple[str, dict[str, Any]]] = []
    if not args.skip_pairs and len(top) >= 2:
        n = 0
        for i, a in enumerate(top):
            for b in top[i + 1 :]:
                if n >= args.max_pairs:
                    break
                ca, cb = a["config"], b["config"]
                if ca is None or cb is None:
                    continue
                lab = f"pair::{a['label']}++{b['label']}"
                pair_cfg = _merge_rules(ca, cb)
                k = _cfg_key(pair_cfg)
                if k in seen:
                    continue
                seen.add(k)
                pair_jobs.append((lab, pair_cfg))
                n += 1
            if n >= args.max_pairs:
                break

    if pair_jobs:
        if args.in_process:
            for pj in pair_jobs:
                results.append(one_job(pj))
        else:
            with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
                futs = [ex.submit(one_job, pj) for pj in pair_jobs]
                for fut in as_completed(futs):
                    results.append(fut.result())

    baseline = next((r for r in results if r["label"] == "baseline"), None)
    ranked = sorted(
        [r for r in results if r.get("feasible")],
        key=lambda r: -r["sort_key"],
    )
    infeas = sorted(
        [r for r in results if not r.get("feasible")],
        key=lambda r: -r.get("sort_key", -1e9),
    )

    payload = {
        "meta": {
            "db": db,
            "holdout_frac": holdout,
            "p_ruin_max": args.p_ruin_max,
            "max_delta_ruin": args.max_delta_ruin,
            "n_jobs_total": len(results),
            "runner_extra": extra,
            "preset": args.preset,
            "in_process": args.in_process,
            "risk": risk,
        },
        "baseline": baseline,
        "best_feasible": ranked[:15],
        "top_infeasible_preview": infeas[:8],
        "all_results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    table_path = out_path.with_name(out_path.stem + "_table.md")
    _write_markdown_table(payload, table_path)
    print(
        json.dumps(
            {"wrote": str(out_path), "table": str(table_path), "n_best_listed": len(ranked[:15])},
            indent=2,
        )
    )

    if ranked:
        best = ranked[0]
        best_cfg_path = out_path.with_name(out_path.stem + "_best_config.json")
        if best.get("config") is not None:
            best_cfg_path.write_text(json.dumps(best["config"], indent=2), encoding="utf-8")
            print(
                json.dumps(
                    {"best_config_written": str(best_cfg_path), "label": best["label"]}, indent=2
                )
            )


if __name__ == "__main__":
    main()
