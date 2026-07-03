"""Phase 3 — correlator: evidence ledger + quantified drift attribution.

For one anomaly window this module assembles everything the library and the
account's own history can say about it:

1. EVENTS — dated signals overlapping (or within ±2d of) the window, with
   direction, severity prior, boundary confidence, and the relation
   (overlap / adjacent-before / adjacent-after). Unverified records are
   excluded (rule 4). Dated events are single-occurrence -> PRIOR ONLY:
   they never carry quantified effect estimates (anti-horoscope rule).
2. RULES — recurring-rule flags inside the window, with account-specific
   coefficients (engine/rules.py) where computed.
3. ACTIVITY — advertiser actions from data/meta/activity_log.* in the window
   or the LOOKBACK_HOURS preceding it, bucketed (budget / status / bid /
   targeting / creative / other). The INTERNAL_ADS evidence stream.

Attribution: observed drift D = mean log(value/expected) over the window for
the window's metric. Only DIRECTION-CONSISTENT, COEFFICIENT-BACKED rule flags
explain drift quantitatively: each contributes its dlog_median, the summed
contribution is capped at |D| (a signal is never stretched to cover
residual), and the remainder is reported as the unexplained residual.
Direction-consistent prior-only events are listed as correlation-only — they
explain 0.0 by construction.
"""

from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from engine import baseline as bl
from engine import rules as rl
from engine.config import DATA_META, REPO_ROOT
from engine.coverage import ADJACENT_DAYS, _event_spans
from engine.decompose import decompose_window

LOOKBACK_HOURS = 72

# Explicit type -> bucket map. Ad-LEVEL run-status flips, review-status
# transitions, billing charges, delivery events, asset uploads and automated
# audience creation are EXCLUDED as noise (the account shows ~7 automated
# ad-status flips/day); campaign/ad-set level actions are the advertiser's
# hand on the wheel.
ACTIVITY_TYPE_BUCKET = {
    "update_campaign_budget": "budget",
    "update_ad_set_budget": "budget",
    "update_campaign_budget_scheduling_state": "budget",
    "ad_account_update_spend_limit": "budget",
    "update_campaign_run_status": "status",
    "update_ad_set_run_status": "status",
    "update_ad_set_bid_strategy": "bid",
    "update_ad_set_bid_adjustments": "bid",
    "update_ad_set_target_spec": "targeting",
    "update_ad_set_optimization_goal": "targeting",
    "create_campaign_group": "structure",
    "create_campaign_legacy": "structure",
    "create_ad_set": "structure",
    "create_ad": "creative",
    "update_ad_creative": "creative",
}

# Which drift sign is "bad" per metric (for direction-consistency of events).
BAD_IS_HIGH = {"cpa": True, "cpm": True, "ctr": False, "cvr": False,
               "spend": None, "checkout_rate": False}  # spend has no bad side a priori


def load_context() -> dict:
    metrics = bl.load_metrics()
    baselines = bl.rolling_baselines(metrics)
    lib = rl.load_library()
    data_end = metrics["date"].max()
    flags = rl.expand_all(metrics["date"].min(), data_end, lib)
    act_path = DATA_META / "activity_log.csv"
    activity = pd.read_csv(act_path, parse_dates=["event_time"]) if act_path.exists() else pd.DataFrame()
    dep_path = REPO_ROOT / "signals" / "deploy_timeline.json"
    deploys = json.loads(dep_path.read_text())["deploy_events"] if dep_path.exists() else []
    return {
        "metrics": metrics, "baselines": baselines, "library": lib,
        "flags": flags, "activity": activity, "deploys": deploys,
        "data_end": data_end, "windows": bl.anomaly_windows(baselines),
    }


def reserved_spans(data_end: dt.date) -> list[tuple[dt.date, dt.date, str]]:
    """Ground-truth incident spans reserved for the Phase 4 blind backtest."""
    inc = json.loads((REPO_ROOT / "backtest" / "incidents.json").read_text())
    spans = []
    for i in inc["testable"]:
        start = dt.date.fromisoformat(i["window_start"])
        if i["window_end"]:
            end = dt.date.fromisoformat(i["window_end"])
        elif i["id"] == "may24-checkout-event-shift":
            end = start  # persistent level shift: reserve windows containing the shift day
        else:
            end = data_end  # live case: reserve everything from onset to data end
        spans.append((start, end, i["id"]))
    return spans


def is_reserved(w: dict, spans) -> str | None:
    for s, e, iid in spans:
        if w["start"] <= e and w["end"] >= s:
            return iid
    return None


def _bucket_activity(event_type: str) -> str | None:
    """Bucket for meaningful advertiser actions; None = noise, excluded."""
    return ACTIVITY_TYPE_BUCKET.get(event_type)


def _direction_consistent(direction: str, metric: str, sign: float) -> bool:
    bad_high = BAD_IS_HIGH[metric]
    if direction == "mixed" or bad_high is None:
        return direction == "mixed"  # mixed matches anything; spend has no bad side
    drift_is_bad = (sign > 0) == bad_high
    return (direction == "suppressive") == drift_is_bad


def ledger_for(w: dict, ctx: dict) -> dict:
    lib, data_end = ctx["library"], ctx["data_end"]
    events = []
    for sig in lib["signals"]:
        if not sig.get("verified"):
            continue  # rule 4: unverified records are excluded from verdicts
        spans = _event_spans(sig, data_end)
        rel = None
        if any(s <= w["end"] and e >= w["start"] for s, e in spans):
            rel = "overlap"
        elif any(0 < (w["start"] - e).days <= ADJACENT_DAYS for s, e in spans):
            rel = "adjacent-before"
        elif any(0 < (s - w["end"]).days <= ADJACENT_DAYS for s, e in spans):
            rel = "adjacent-after"
        if rel:
            events.append({
                "id": sig["id"], "layer": sig["layer"], "relation": rel,
                "direction": sig.get("direction", "mixed"),
                "severity_prior": sig.get("severity_prior"),
                "boundary_confidence": sig.get("boundary_confidence", "normal"),
                "quantified": False,  # dated events are single-occurrence: prior only
            })

    in_win = ctx["flags"][(ctx["flags"]["date"] >= w["start"]) & (ctx["flags"]["date"] <= w["end"])]
    window_days = (w["end"] - w["start"]).days + 1
    rules = []
    for rid, grp in in_win.groupby("rule_id"):
        rule = lib["rules"][rid]
        coefs = (rule.get("coefficients") or {})
        rules.append({
            "id": rid, "layer": rule["layer"], "direction": rule.get("direction", "mixed"),
            "coefficient": (coefs.get("metrics") or {}).get(w["metric"]),
            "status": coefs.get("status", "prior only"),
            "all_metrics": coefs.get("metrics"),
            "days_flagged": int(grp["date"].nunique()),
            "day_weight": grp["date"].nunique() / window_days,
        })

    activity = []
    act = ctx["activity"]
    if not act.empty:
        tz = act["event_time"].dt.tz
        t0 = pd.Timestamp(w["start"]).tz_localize(tz) - pd.Timedelta(hours=LOOKBACK_HOURS)
        t1 = pd.Timestamp(w["end"]).tz_localize(tz) + pd.Timedelta(days=1)
        sel = act[(act["event_time"] >= t0) & (act["event_time"] < t1)].copy()
        sel["bucket"] = sel["event_type"].map(ACTIVITY_TYPE_BUCKET)
        sel = sel.dropna(subset=["bucket"])
        sel["when"] = ["pre-window" if t.date() < w["start"] else "in-window"
                       for t in sel["event_time"]]
        for (bucket, etype, when), grp in sel.groupby(["bucket", "event_type", "when"]):
            objs = grp["object_name"].dropna().unique()[:3].tolist()
            activity.append({
                "bucket": bucket, "event_type": etype, "when": when,
                "count": int(len(grp)),
                "first_time": grp["event_time"].min().isoformat(),
                "objects_sample": objs,
            })
    # SITE_DEPLOY stream — earliest-possible-live semantics: commit time is a
    # LOWER bound on live time, so a deploy dated D is an onset candidate only
    # for windows with start >= D (within the lookback); a deploy after onset
    # is tail-shaping or reactive, never an onset cause.
    deploys = []
    for dep in ctx["deploys"]:
        d = dt.date.fromisoformat(dep["date"])
        if d < w["start"] - dt.timedelta(days=LOOKBACK_HOURS // 24) or d > w["end"]:
            continue
        deploys.append({
            "id": dep["id"], "date": d,
            "layer_candidate": dep["layer_candidate"],
            "n_commits": len(dep["commits"]),
            "publish_time_confirmed": dep["publish_time_confirmed"],
            "verified_mechanism": (dep.get("verification") or {}).get("result") == "CONFIRMED",
            "timing": ("pre-onset" if d < w["start"] else
                       "onset-day" if d == w["start"] else "post-onset"),
        })
    return {"events": events, "rules": rules, "activity": activity,
            "deploys": deploys, "deploy_stream_available": bool(ctx["deploys"]),
            "activity_log_available": not act.empty}


def attribute(w: dict, ledger: dict, ctx: dict) -> dict:
    """Quantified attribution of the window's drift. See module docstring."""
    b = ctx["baselines"]
    g = b[(b["metric"] == w["metric"]) & (b["date"] >= w["start"]) &
          (b["date"] <= w["end"])].dropna(subset=["z"])
    D = float(np.log(g["value"] / g["expected"]).mean())
    sign = float(np.sign(D))

    explained, budget_used = [], 0.0
    for r in ledger["rules"]:
        c = r["coefficient"]
        if not c or np.sign(c["dlog_median"]) != sign:
            continue  # prior-only or direction-inconsistent: explains nothing
        # A rule flagged on k of the window's n days can move the WINDOW MEAN
        # by at most k/n of its per-day coefficient — never more.
        expected = abs(c["dlog_median"]) * r["day_weight"]
        room = max(abs(D) - budget_used, 0.0)
        take = min(expected, room)
        budget_used += take
        explained.append({"id": r["id"], "kind": "rule-coefficient",
                          "dlog": sign * take, "raw_dlog": c["dlog_median"],
                          "day_weight": r["day_weight"], "n_days": c["n_days"]})

    correlation_only = [e["id"] for e in ledger["events"]
                        if _direction_consistent(e["direction"], w["metric"], sign)]
    out = {
        "observed_dlog": D,
        "observed_pct": float(np.exp(D) - 1),
        "explained": explained,
        "explained_dlog": float(sign * budget_used),
        "explained_share": float(min(budget_used / abs(D), 1.0)) if D else 0.0,
        "residual_dlog": float(D - sign * budget_used),
        "correlation_only": correlation_only,
    }
    if w["metric"] == "cpa":
        out["decomposition"] = decompose_window(ctx["baselines"], w["start"], w["end"])
    return out
