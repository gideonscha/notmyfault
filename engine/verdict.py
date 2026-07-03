"""Phase 3 — verdict engine + per-window reports (brief §4 classes, §7 format).

Deterministic, auditable rule cascade over the correlator's evidence ledger.
Thresholds are v1 heuristics, to be calibrated against the Phase 4 blind
backtest — they are constants below, not buried logic.

Cascade (first strong match wins; weaker matches become MIXED components or
rejections):

  R0 REPORTING_ARTIFACT — checked FIRST (cheapest verdict):
     (a) window's metric is measured across a known measurement-shift ACCOUNT
         event (e.g. checkout-event definition change), or
     (b) window sits inside the trailing attribution-lag zone of the data
         (ends within LAG_ZONE_DAYS of data end) with a bad CVR/CPA/checkout
         drift — conversions may still back-fill.
  R1 INTERNAL_ADS — advertiser's own actions: budget/status/bid/targeting
     activity in the window or the preceding 72h. STRONG for spend windows
     (the action directly moves the metric); SUPPORTING for cpa/cpm/cvr.
     If the activity log is unavailable, this class is UNTESTABLE, not
     rejected — stated explicitly.
  R2 Quantified rule coefficients + direction-consistent events, allocated
     by layer (EXTERNAL_DEMAND / EXTERNAL_AUCTION / EXTERNAL_PLATFORM).
     CPA windows also use the decomposition pattern (brief §4 table):
     CPM-dominant -> EXTERNAL_AUCTION candidate; CVR-dominant with demand
     evidence -> EXTERNAL_DEMAND; CTR-dominant without creative-change
     evidence stays unattributed (creative fatigue is NOT assumed).
  R3 MIXED — two classes each carry >= MIXED_MIN_SHARE of explained drift
     (or strong INTERNAL_ADS + a quantified external class): report the
     quantified split.
  R4 UNEXPLAINED — explained_share < UNEXPLAINED_BELOW and no strong
     class evidence. A legitimate verdict: residual is never assigned to
     the nearest plausible story. INTERNAL_FUNNEL is only ever assigned on
     site-change evidence, which no current stream provides — it can appear
     only via future evidence streams.

Confidence = explained_share for coefficient-backed verdicts, with a bonus
for corroborating correlation-only events (+0.05 each, max +0.15), 0.85 base
for direct INTERNAL_ADS evidence on spend windows, 0.9 for measurement-shift
REPORTING_ARTIFACT. UNEXPLAINED confidence = 1 - explained_share (confidence
that known signals do NOT explain it). Bands: HIGH >= 0.7 / MEDIUM >= 0.4 /
LOW below.

Usage: python -m engine.verdict          # all non-reserved windows
Ground-truth incident windows (backtest/incidents.json testable) are SKIPPED
— reserved for the Phase 4 blind backtest.
"""

from __future__ import annotations

import numpy as np

from engine import correlate as co
from engine.config import REPO_ROOT

VERDICT_DIR = REPO_ROOT / "reports" / "verdicts"

LAG_ZONE_DAYS = 3
MIXED_MIN_SHARE = 0.25
UNEXPLAINED_BELOW = 0.40
DOMINANT_SHARE = 0.50

LAYER_CLASS = {"EXTERNAL_DEMAND": "EXTERNAL_DEMAND",
               "EXTERNAL_AUCTION": "EXTERNAL_AUCTION",
               "EXTERNAL_PLATFORM": "EXTERNAL_PLATFORM"}


def _band(c: float) -> str:
    return "HIGH" if c >= 0.7 else "MEDIUM" if c >= 0.4 else "LOW"


def classify(w: dict, ledger: dict, attr: dict, ctx: dict) -> dict:
    D = attr["observed_dlog"]
    sign = np.sign(D)
    bad_high = co.BAD_IS_HIGH[w["metric"]]
    drift_is_bad = bad_high is not None and (sign > 0) == bad_high
    rejected: list[tuple[str, str]] = []
    lib_rules = ctx["library"]["rules"]

    # ---- R0: REPORTING_ARTIFACT ----
    measurement_events = [e for e in ledger["events"]
                          if e["id"].startswith("acct-checkout-event-shift")
                          and w["metric"] == "checkout_rate" and e["relation"] == "overlap"]
    if measurement_events:
        return {"verdict": "REPORTING_ARTIFACT", "confidence": 0.9, "band": _band(0.9),
                "reason": f"{measurement_events[0]['id']}: metric is measured across a known "
                          "event-definition shift — level change, not behavior change.",
                "rejected": rejected, "split": None}
    in_lag_zone = (ctx["data_end"] - w["end"]).days <= LAG_ZONE_DAYS
    if in_lag_zone and w["metric"] in ("cpa", "cvr", "checkout_rate") and drift_is_bad:
        return {"verdict": "REPORTING_ARTIFACT", "confidence": 0.5, "band": _band(0.5),
                "reason": "window ends inside the trailing attribution-lag zone; conversions "
                          "may back-fill — re-verdict after the lag curve settles.",
                "rejected": rejected, "split": None}
    rejected.append(("REPORTING_ARTIFACT",
                     "no measurement-shift event on this metric; window is "
                     f"{(ctx['data_end'] - w['end']).days}d before data end, outside the "
                     f"{LAG_ZONE_DAYS}d attribution-lag zone"))

    # ---- R1: INTERNAL_ADS (timing-disciplined) ----
    # Activity timestamps are UTC; insight days are account-local. An event
    # dated start+1 with an early UTC hour is often still the onset evening
    # locally — delta==1 is treated as ambiguous, not post-onset.
    act_relevant = [a for a in ledger["activity"]
                    if a["bucket"] in ("budget", "status", "bid", "targeting", "structure")]
    internal_ads, act_note = None, None
    if act_relevant:
        import datetime as _dt
        earliest = min(a["first_time"] for a in act_relevant)
        delta = (_dt.date.fromisoformat(earliest[:10]) - w["start"]).days
        buckets = ", ".join(sorted({a["bucket"] for a in act_relevant}))
        if w["metric"] == "spend":
            conf, note = ((0.85, "") if delta <= 0 else
                          (0.75, " Earliest action is dated onset+1 in UTC — likely onset evening "
                                 "account-local (timezone skew).") if delta == 1 else
                          (0.6, f" CAVEAT: earliest recorded action is {delta}d after onset — explains "
                                "the continuation, not the onset; unlogged automated pacing may act earlier."))
            internal_ads = {"strong": True, "events": act_relevant, "conf": conf, "note": note}
        else:
            if delta <= 0:
                act_note = (f"Advertiser actions ({buckets}) in the {co.LOOKBACK_HOURS}h before/at onset — "
                            "INTERNAL_ADS candidate, unquantified (v1 has no effect model for non-spend metrics).")
            elif delta == 1:
                act_note = (f"Advertiser actions ({buckets}) first recorded onset+1 (UTC; possibly onset "
                            "evening account-local) — ambiguous INTERNAL_ADS candidate, unquantified.")
            else:
                rejected.append(("INTERNAL_ADS (as onset cause)",
                                 f"meaningful account changes ({buckets}) begin {delta}d after onset — "
                                 "timing indicates reaction to the anomaly, not cause; may affect the window tail"))
    elif not ledger["activity_log_available"]:
        rejected.append(("INTERNAL_ADS", "UNTESTABLE — activity log unavailable for this window "
                                         "(endpoint retention); absence of evidence, not evidence of absence"))
    else:
        rejected.append(("INTERNAL_ADS", "no budget/status/bid/targeting/structure changes in-window or "
                                         f"in the preceding {co.LOOKBACK_HOURS}h"))

    # ---- R2: quantified layers ----
    layer_dlog: dict[str, float] = {}
    for x in attr["explained"]:
        layer = lib_rules[x["id"]]["layer"]
        cls = LAYER_CLASS.get(layer)
        if cls:
            layer_dlog[cls] = layer_dlog.get(cls, 0.0) + abs(x["dlog"])
    corroborating = {}
    for e in ledger["events"]:
        if e["id"] in attr["correlation_only"]:
            cls = LAYER_CLASS.get(e["layer"])
            if cls:
                corroborating.setdefault(cls, []).append(e["id"])
    for e in ledger["events"]:
        if e["id"] not in attr["correlation_only"] and e["layer"] in LAYER_CLASS:
            rejected.append((LAYER_CLASS[e["layer"]],
                             f"{e['id']} overlaps but its direction ({e['direction']}) is "
                             "inconsistent with the observed drift"))

    # CPA decomposition pattern (brief §4)
    decomp_note = None
    if w["metric"] == "cpa" and "decomposition" in attr:
        comps = attr["decomposition"]["components"]
        shares = {m: c["share_of_cpa_drift"] for m, c in comps.items()}
        valid = {m: s for m, s in shares.items() if s == s}
        if valid:
            dom, dom_share = max(valid.items(), key=lambda kv: kv[1])
            if dom == "cpm" and dom_share >= DOMINANT_SHARE:
                decomp_note = ("cpm", dom_share)
                corroborating.setdefault("EXTERNAL_AUCTION", []).append(
                    f"decomposition: CPM carries {dom_share:.0%} of CPA drift")
            elif dom == "cpm" and dom_share < 0:
                rejected.append(("EXTERNAL_AUCTION",
                                 f"CPM moved opposite the drift (share {dom_share:.0%}) — auction got "
                                 "cheaper while CPA worsened" if D > 0 else
                                 f"CPM share {dom_share:.0%} inconsistent"))
            if dom == "ctr" and dom_share >= DOMINANT_SHARE:
                has_creative = any(a["bucket"] == "creative" for a in ledger["activity"])
                decomp_note = ("ctr", dom_share)
                if not has_creative:
                    rejected.append(("creative-fatigue", f"CTR carries {dom_share:.0%} of drift but no "
                                                         "creative changes in activity log — fatigue vs "
                                                         "delivery-shift unresolved, NOT assumed"))
            if dom == "cvr" and dom_share >= DOMINANT_SHARE:
                decomp_note = ("cvr", dom_share)
        if shares.get("cpm", 0) == shares.get("cpm", 0) and shares.get("cpm", 1) < 0 and D > 0:
            rejected.append(("EXTERNAL_AUCTION", f"CPM share of drift is {shares['cpm']:.0%} — CPM moved "
                                                 "in the account's favor during this window"))

    # ---- verdict selection ----
    total_explained = attr["explained_share"]
    candidates = sorted(layer_dlog.items(), key=lambda kv: -kv[1])
    split = None

    if internal_ads and internal_ads["strong"]:
        cls, conf = "INTERNAL_ADS", internal_ads["conf"]
        reason = (f"{sum(a['count'] for a in internal_ads['events'])} advertiser action(s) "
                  f"({', '.join(sorted({a['bucket'] for a in internal_ads['events']}))}) in-window or "
                  f"preceding {co.LOOKBACK_HOURS}h directly move spend." + internal_ads["note"])
        if candidates and abs(D) > 0 and (candidates[0][1] / abs(D)) >= MIXED_MIN_SHARE:
            other, odl = candidates[0]
            split = {"INTERNAL_ADS": 1 - odl / abs(D), other: odl / abs(D)}
            cls = "MIXED"
            reason += f" MIXED with {other}: coefficient-backed rules explain {odl/abs(D):.0%} of drift."
        return {"verdict": cls, "confidence": conf, "band": _band(conf),
                "reason": reason, "rejected": rejected, "split": split,
                "internal_ads_events": internal_ads["events"]}

    if candidates and abs(D) > 0:
        shares = {c: dl / abs(D) for c, dl in candidates}
        top, top_share = candidates[0][0], candidates[0][1] / abs(D)
        second = [(c, s) for c, s in shares.items() if c != top and s >= MIXED_MIN_SHARE]
        if total_explained >= UNEXPLAINED_BELOW:
            n_corr = len(corroborating.get(top, []))
            conf = min(total_explained + 0.05 * min(n_corr, 3), 0.95)
            if second:
                split = {c: round(s, 2) for c, s in shares.items()}
                split["UNEXPLAINED"] = round(1 - sum(shares.values()), 2)
                cls, reason = "MIXED", (f"quantified split across {len(shares)} layers; "
                                        f"residual {1-total_explained:.0%} left unexplained.")
            else:
                cls = top
                reason = (f"coefficient-backed rules explain {total_explained:.0%} of drift, "
                          f"led by {top} ({top_share:.0%})"
                          + (f"; corroborated by {n_corr} correlation-only event(s)" if n_corr else "")
                          + f"; residual {1-total_explained:.0%} unexplained.")
            if act_note:
                reason += " " + act_note
            return {"verdict": cls, "confidence": conf, "band": _band(conf),
                    "reason": reason, "rejected": rejected, "split": split,
                    "corroborating": corroborating, "decomp_note": decomp_note}

    # ---- R4: UNEXPLAINED ----
    conf = 1 - total_explained
    n_corr = len(attr["correlation_only"])
    reason = (f"coefficient-backed evidence explains only {total_explained:.0%} of the drift"
              + (f"; {n_corr} direction-consistent event(s) overlap but are prior-only "
                 "(correlation only, coefficient unknown) and are NOT stretched to cover the residual"
                 if n_corr else "; no direction-consistent signals in the library") + ".")
    if act_note:
        reason += " " + act_note
    return {"verdict": "UNEXPLAINED", "confidence": conf, "band": _band(conf),
            "reason": reason, "rejected": rejected, "split": None,
            "corroborating": corroborating, "decomp_note": decomp_note}


def render_report(w: dict, ledger: dict, attr: dict, v: dict, ctx: dict, wid: str) -> str:
    arrow = "▲" if w["direction"] == "high" else "▼"
    L = []
    add = L.append
    add(f"# {wid} — {w['metric'].upper()} {arrow} {attr['observed_pct']:+.1%} · "
        f"{w['start']} .. {w['end']}")
    add("")
    add(f"**VERDICT: {v['verdict']}** (confidence {v['confidence']:.2f} — {v['band']})")
    add("")
    add(v["reason"])
    if v.get("split"):
        add("")
        add("Quantified split: " + ", ".join(f"{k} {s:.0%}" for k, s in v["split"].items()))
    add("")
    add("## The numbers")
    add("")
    add(f"- {w['days']} consecutive days beyond ±{2.0:g}σ (mean z {w['mean_z']:+.1f}, "
        f"peak z {w['peak_z']:+.1f}) vs the day-of-week-adjusted trailing-90d baseline")
    add(f"- drift: {attr['observed_pct']:+.1%} vs baseline (dlog {attr['observed_dlog']:+.3f})")
    if "decomposition" in attr:
        add("- CPA decomposition (share of drift): " + ", ".join(
            f"{m.upper()} {c['pct_vs_baseline']:+.1%} ({c['share_of_cpa_drift']:.0%})"
            for m, c in attr["decomposition"]["components"].items()
            if c["share_of_cpa_drift"] == c["share_of_cpa_drift"]))
    add("")
    add("## Evidence ledger")
    add("")
    add("| evidence | type | relation | direction | quantified effect | explains |")
    add("|---|---|---|---|---|---|")
    explained_by = {x["id"]: x for x in attr["explained"]}
    for r in ledger["rules"]:
        x = explained_by.get(r["id"])
        c = r["coefficient"]
        eff = f"{c['pct_effect']:+.1%} (n={c['n_days']})" if c else "prior only"
        add(f"| {r['id']} | rule ({r['layer']}) | in-window | {r['direction']} | {eff} | "
            f"{'dlog ' + format(x['dlog'], '+.3f') if x else '—'} |")
    for e in ledger["events"]:
        corr = "correlation only" if e["id"] in attr["correlation_only"] else "direction-inconsistent"
        add(f"| {e['id']} | event ({e['layer']}) | {e['relation']} | {e['direction']} | "
            f"prior only ({corr}) | — |")
    for a in ledger["activity"]:
        objs = ", ".join(a["objects_sample"][:2]) or "—"
        add(f"| {a['event_type']} ×{a['count']} ({objs}) | account activity [{a['bucket']}] | "
            f"{a['when']}, first {a['first_time'][:16]} | — | direct advertiser action | — |")
    if not ledger["activity"] and not ledger["activity_log_available"]:
        add("| _activity log_ | account activity | — | — | UNAVAILABLE for this window | — |")
    add("")
    add("## Attribution")
    add("")
    add(f"- observed drift: dlog {attr['observed_dlog']:+.3f}")
    add(f"- explained by coefficient-backed signals: dlog {attr['explained_dlog']:+.3f} "
        f"({attr['explained_share']:.0%})")
    add(f"- **unexplained residual: dlog {attr['residual_dlog']:+.3f} "
        f"({1 - attr['explained_share']:.0%} of drift)**")
    add("")
    add("## What it is NOT")
    add("")
    for cls, why in v["rejected"]:
        add(f"- **NOT {cls}**: {why}")
    if not v["rejected"]:
        add("- (no candidate hypotheses were rejected)")
    add("")
    add("## Caveats")
    add("")
    add("- Thresholds are v1 heuristics pending Phase 4 backtest calibration.")
    add("- Baselines carry ~7.5 months of history; month-position effects are "
        "diagnostics only and not removed from z-scores.")
    if any(e.get("boundary_confidence") == "low" for e in ledger["events"]):
        add("- One or more matched events have LOW boundary confidence (window edges are "
            "conventional, not measured).")
    add("")
    return "\n".join(L)


def main() -> None:
    ctx = co.load_context()
    spans = co.reserved_spans(ctx["data_end"])
    VERDICT_DIR.mkdir(parents=True, exist_ok=True)
    written, skipped = [], []
    for i, w in enumerate(ctx["windows"], 1):
        wid = f"w{i:02d}_{w['metric']}_{w['start']}"
        reserved = co.is_reserved(w, spans)
        if reserved:
            skipped.append((wid, reserved))
            continue
        ledger = co.ledger_for(w, ctx)
        attr = co.attribute(w, ledger, ctx)
        v = classify(w, ledger, attr, ctx)
        (VERDICT_DIR / f"{wid}.md").write_text(render_report(w, ledger, attr, v, ctx, wid))
        written.append((wid, v["verdict"], v["confidence"]))
    print(f"[verdict] {len(written)} verdicts -> {VERDICT_DIR.relative_to(REPO_ROOT)}/ | "
          f"{len(skipped)} windows reserved for Phase 4 blind backtest")
    for wid, verd, conf in written:
        print(f"  {wid:>28s}  {verd:<18s} conf {conf:.2f}")
    for wid, iid in skipped:
        print(f"  {wid:>28s}  RESERVED ({iid})")


if __name__ == "__main__":
    main()
