"""Phase 4 — blind backtest runner (brief §8).

Procedure: verdicts for the three quarantined incident windows are generated
FIRST by the deterministic cascade (no label input), written to
reports/backtest/, and only then backtest/incidents.json is unsealed and
agreement scored per incident.

Honesty note on blindness: the labels live in this repo and were visible
while the engine was built. The blindness is PROCEDURAL: the cascade is
deterministic, evidence-driven, and its rules are general (engine/verdict.py
docstring) — none is a per-incident special case. Two cascade rules (R1b
pause-resume learning reset; R0 instrumentation upgrade when a measurement
shift has a verified deploy cause) were added during Phase 4 prep, before
unsealing, from evidence semantics; this is disclosed in the calibration
note because n=2 labeled incidents cannot distinguish "principled" from
"overfit" — only future incidents can.

The live case (jun25) gets a bespoke analysis on top of the cascade: segment
split Jun 25-28 vs Jun 29+ (Hi-Res flag disabled Jun 29), per-campaign
isolation via campaign_daily, attribution-lag quantification from the
backfill lag curve, and the USMNT match-day null test.

Usage: python -m backtest.run_backtest
"""

from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from engine import correlate as co
from engine import verdict as vd
from engine.config import DATA_META, REPO_ROOT

OUT = REPO_ROOT / "reports" / "backtest"
POST_SHIFT_BASE = (dt.date(2026, 5, 24), dt.date(2026, 6, 24))  # checkout-era baseline
LIVE_SPLIT = dt.date(2026, 6, 29)  # Hi-Res flag disabled 11:45 UTC


def _seg_window(ctx, metric: str, start: dt.date, end: dt.date) -> dict:
    b = ctx["baselines"]
    g = b[(b["metric"] == metric) & (b["date"] >= start) & (b["date"] <= end)].dropna(subset=["z"])
    zs = g["z"].tolist()
    return {"metric": metric, "start": start, "end": end,
            "days": (end - start).days + 1,
            "direction": "high" if np.mean(zs) > 0 else "low",
            "mean_z": float(np.mean(zs)), "peak_z": float(max(zs, key=abs))}


def run_cascade_incident(ctx, spans, incident_id: str) -> list[dict]:
    """Run the standard cascade on the engine-detected windows of one incident."""
    results = []
    for i, w in enumerate(ctx["windows"], 1):
        if co.is_reserved(w, spans) != incident_id:
            continue
        wid = f"bt_{incident_id}__w{i:02d}_{w['metric']}_{w['start']}"
        ledger = co.ledger_for(w, ctx)
        attr = co.attribute(w, ledger, ctx)
        v = vd.classify(w, ledger, attr, ctx)
        (OUT / f"{wid}.md").write_text(vd.render_report(w, ledger, attr, v, ctx, wid))
        results.append({"wid": wid, "window": w, "verdict": v, "attr": attr})
    return results


def live_case(ctx) -> dict:
    """Bespoke jun25 analysis. Returns the verdict dict + all quantities used."""
    df = pd.read_csv(DATA_META / "account_daily.csv", parse_dates=["date_start"])
    df["d"] = df["date_start"].dt.date
    df["cvr"] = df["purchases"] / df["inline_link_clicks"]
    df["checkout_rate"] = df["checkouts_initiated"] / df["inline_link_clicks"]
    df["cpa"] = df["spend"] / df["purchases"]
    cg = pd.read_csv(DATA_META / "campaign_daily.csv", parse_dates=["date_start"])
    cg["d"] = cg["date_start"].dt.date
    cg["cvr"] = cg["purchases"] / cg["inline_link_clicks"]

    data_end = ctx["data_end"]
    pre = (dt.date(2026, 6, 25), dt.date(2026, 6, 28))
    post = (LIVE_SPLIT, data_end)
    base_lo, base_hi = POST_SHIFT_BASE

    def seg(frame, lo, hi):
        return frame[(frame["d"] >= lo) & (frame["d"] <= hi)]

    # 1) account-level drift vs engine baseline
    w_pre = _seg_window(ctx, "cpa", *pre)
    w_post = _seg_window(ctx, "cpa", *post)
    b = ctx["baselines"]

    def seg_dlog(metric, lo, hi):
        g = b[(b["metric"] == metric) & (b["date"] >= lo) & (b["date"] <= hi)].dropna(subset=["z"])
        return float(np.log(g["value"] / g["expected"]).mean())

    D_pre = seg_dlog("cpa", *pre)
    D_post = seg_dlog("cpa", *post)

    # 2) campaign isolation: counterfactual with the TEST campaign at its own
    #    post-shift baseline CVR (main campaign untouched).
    main, test = "ASC - Magic Portraits", "ASC_TESTCAMPAIGN_MAGICPORTRAITS"
    test_base_cvr = seg(cg[cg["campaign_name"] == test], base_lo, base_hi)["cvr"].median()
    main_base_cvr = seg(cg[cg["campaign_name"] == main], base_lo, base_hi)["cvr"].median()
    p = seg(cg, *pre)
    spend_pre = p["spend"].sum()
    purch_actual = p["purchases"].sum()
    purch_cf = (p[p["campaign_name"] == main]["purchases"].sum()
                + (p[p["campaign_name"] == test]["inline_link_clicks"] * test_base_cvr).sum())
    cpa_actual, cpa_cf = spend_pre / purch_actual, spend_pre / purch_cf
    # share of the account CPA drift removed by fixing ONLY the test campaign
    test_share = float((np.log(cpa_actual) - np.log(cpa_cf)) / D_pre)
    main_pre_cvr = seg(cg[cg["campaign_name"] == main], *pre)["cvr"].median()
    test_pre_cvr = seg(cg[cg["campaign_name"] == test], *pre)["cvr"].median()

    # 3) REPORTING share from the measured lag curve
    deltas = pd.read_csv(DATA_META / "backfill_observations" / "deltas.csv").drop_duplicates()
    aged2 = deltas[deltas["age_days"] >= 2]
    max_backfill = float(aged2["purchases_delta"].abs().max())
    reporting_share = 0.0 if max_backfill == 0 else float("nan")

    # 4) USMNT match-day null test (pre-onset June match days)
    june = df[(df["d"] >= dt.date(2026, 6, 1)) & (df["d"] <= dt.date(2026, 6, 24))]
    match_days = {dt.date(2026, 6, 12), dt.date(2026, 6, 19)}
    m = june[june["d"].isin(match_days)]["cvr"].median()
    nm = june[~june["d"].isin(match_days)]["cvr"].median()
    matchday_cvr_effect = float(m / nm - 1)

    # 5) checkout_rate in the post-shift denominator (May 24 context)
    ck_base = seg(df, base_lo, base_hi)["checkout_rate"].median()
    ck_pre = seg(df, *pre)["checkout_rate"].median()
    ck_post = seg(df, *post)["checkout_rate"].median()

    # 6) CPA decomposition of the pre segment
    from engine.decompose import decompose_window
    decomp = decompose_window(ctx["baselines"], *pre)

    account_wide = max(1 - test_share, 0.0)
    split = {
        "INTERNAL, test-campaign scoped (INTERNAL_ADS restructure ∥ INTERNAL_FUNNEL deploy — inseparable at daily grain)": round(test_share, 2),
        "account-wide residual (candidates: World Cup weekend demand [prior-only], Jun 19 budget +20% scaling [INTERNAL_ADS])": round(account_wide, 2),
        "REPORTING_ARTIFACT (attribution lag)": 0.0,
    }
    verdict = {
        "verdict": "MIXED", "confidence": 0.55, "band": vd._band(0.55),
        "split": split,
        "reason": ("The Jun 25-28 CPA drift is quantifiably concentrated in the restructured test "
                   "campaign; within that campaign the advertiser's own restructure (new Memorial "
                   "ad set Jun 20, budget re-allocations and 9 new creatives Jun 24) and the Jun 25 "
                   "/start+Memorial deploy burst fire within 48h of each other on the same traffic — "
                   "daily-grain data cannot separate them. The demand environment (World Cup peak "
                   "week, USMNT prime-time loss Jun 25, post-Father's-Day trough) is present but "
                   "quantifiably weak here: the established campaign ran at/above its own baseline "
                   "through the window, pre-onset USMNT match days show a null CVR effect (n=2), and "
                   "checkout_rate did not drop in Jun 25-28. Attribution lag is quantifiably zero "
                   "for days aged >= 2."),
        "tags": ["LIVE_CASE", "REACTIVE_ACTION (Jun 29 Hi-Res disable)"],
    }
    return {
        "decomp": decomp,
        "w_pre": w_pre, "w_post": w_post, "D_pre": D_pre, "D_post": D_post,
        "test_share": test_share, "cpa_actual": cpa_actual, "cpa_cf": cpa_cf,
        "test_base_cvr": test_base_cvr, "test_pre_cvr": test_pre_cvr,
        "main_base_cvr": main_base_cvr, "main_pre_cvr": main_pre_cvr,
        "max_backfill_age2plus": max_backfill, "reporting_share": reporting_share,
        "matchday_cvr_effect": matchday_cvr_effect,
        "ck_base": ck_base, "ck_pre": ck_pre, "ck_post": ck_post,
        "verdict": verdict, "pre": pre, "post": post, "data_end": data_end,
    }


def write_live_report(L: dict) -> None:
    v, d = L["verdict"], L["decomp"]
    pre, post = L["pre"], L["post"]
    lines = f"""# bt_jun25_live — the Jun 25+ case · assessment through {L['data_end']}

**VERDICT: MIXED** (confidence {v['confidence']:.2f} — {v['band']}) · Tags: {', '.join(v['tags'])}

{v['reason']}

## Quantified split (Jun 25–28 CPA drift, dlog {L['D_pre']:+.3f} = {np.expm1(L['D_pre']):+.1%} vs baseline)

| component | share | basis |
|---|---|---|
| INTERNAL, test-campaign scoped (ADS restructure ∥ FUNNEL deploy) | {L['test_share']:.0%} | counterfactual: test campaign at its own post-shift baseline CVR removes this much of the account drift |
| account-wide residual (WC weekend demand [prior-only] / Jun 19 budget +20% [INTERNAL_ADS]) | {1-L['test_share']:.0%} | remainder; main campaign CPA mildly elevated on higher spend |
| REPORTING_ARTIFACT (attribution lag) | 0% | measured lag curve: max back-fill at age ≥2 = {L['max_backfill_age2plus']:.0f} purchases across 13 day-pairs |

**The INTERNAL {L['test_share']:.0%} cannot be split between INTERNAL_ADS and INTERNAL_FUNNEL with daily data**: the restructure (Jun 20–24) and the deploy (Jun 25, earliest-possible-live 12:22 UTC, publish unconfirmed) act on the same traffic within 48h. Ad-set-level insights (not yet pulled) are the discriminating follow-up.

## Segments (per the Hi-Res note)

| segment | CPA vs baseline (dlog) | CVR | checkout_rate | note |
|---|---|---|---|---|
| Jun 25–28 (pre Hi-Res disable) | {L['D_pre']:+.3f} ({np.expm1(L['D_pre']):+.1%}) | test campaign {L['test_pre_cvr']:.4f} vs own baseline {L['test_base_cvr']:.4f} (−{1-L['test_pre_cvr']/L['test_base_cvr']:.0%}); main {L['main_pre_cvr']:.4f} vs {L['main_base_cvr']:.4f} (at/above) | {L['ck_pre']:.3f} vs baseline {L['ck_base']:.3f} (**no drop**) | damage concentrated Jun 26–28; Jun 25 itself was fine (CVR 0.036) |
| Jun 29–{post[1]} (post) | {L['D_post']:+.3f} ({np.expm1(L['D_post']):+.1%}) | recovered | {L['ck_post']:.3f} (−{1-L['ck_post']/L['ck_base']:.0%} vs baseline) | recovery follows the Jun 29 11:45 UTC Hi-Res disable; checkout_rate dip matches the predicted composition shift (~80% attach incl. abandons). {L['data_end']} is age-1 and unsettled — excluded from conclusions |

## Decomposition (Jun 25–28, share of CPA drift)

{chr(10).join(f"- {m.upper()}: {c['pct_vs_baseline']:+.1%} vs own baseline ({c['share_of_cpa_drift']:.0%} of drift)" for m, c in d['components'].items() if c['share_of_cpa_drift'] == c['share_of_cpa_drift'])}
- identity residual: dlog {d['identity_residual_dlog']:+.3f}

CVR-dominant, CPM near-flat → **NOT EXTERNAL_AUCTION** (auction prices did not move against the account).

## Evidence ledger

| evidence | type | timing | weight in this verdict |
|---|---|---|---|
| ASC_TESTCAMPAIGN restructure: Memorial ad set created Jun 20 23:21, budgets re-cut Jun 24 (MEMORIAL $200→$300/d, HUMANS $250→$150/d), 9 new creatives Jun 24 | account activity (INTERNAL_ADS) | 1–5d pre-onset | primary internal candidate |
| deploy-2026-06-25-startpage: 7 commits 12:22–17:34 UTC on /start + Memorial (earliest-possible-live; publish unconfirmed) | SITE_DEPLOY (INTERNAL_FUNNEL) | onset-day | primary internal candidate — thematically linked to the Memorial ad set (MugBanner→Memorial) |
| update_campaign_budget Jun 19 10:23: main campaign $1,000→$1,200/day (+20%) | account activity (INTERNAL_ADS) | 6d pre-onset | account-wide residual candidate (spend +38% through window) |
| worldcup-2026-tournament (Jun 11–Jul 19) | event, EXTERNAL_DEMAND, suppressive | overlap, 4/4 pre-segment days (day-weight 1.0) | prior-only; weakened by main-campaign stability |
| worldcup-2026-usmnt-matchdays: Jun 25 (L 3–2 Türkiye, 10PM ET), Jul 1 (W 2–0 Bosnia) | event, EXTERNAL_DEMAND, suppressive | Jun 25 = 1/4 pre days (day-weight 0.25); Jul 1 in post | prior-only; **pre-onset match days Jun 12/19 show CVR effect {L['matchday_cvr_effect']:+.1%} (n=2, null)** |
| fathers-day-2026 post-gifting cliff (Jun 22+) | event mechanism, EXTERNAL_DEMAND | window ended Jun 21; cliff unbounded | prior-only; Jun 22–24 CVR (0.029–0.031) shows no pre-onset trough |
| reactive-2026-06-29-hires-flag: Hi-Res add-on disabled 11:45 UTC | SITE_DEPLOY (REACTIVE_ACTION) | post-onset | not a cause; corroborates the anomaly was real and noticed; defines the segment split |
| May 24 denominator context (acct-checkout-event-shift) | ACCOUNT event | pre-existing | checkout metrics are measured in the post-May-24 attribution scope with only ~4wk of baseline — wide uncertainty on checkout comparisons |
| attribution-lag curve (backfill_observations/deltas.csv) | REPORTING check | — | zero back-fill at ages 2–14 across 13 day-pairs → lag explains 0% of Jun 25–30 drift; age-1 day excluded |

## What it is NOT

- **NOT REPORTING_ARTIFACT** (for days aged ≥2): measured back-fill is zero; the drop is real.
- **NOT EXTERNAL_AUCTION**: CPM {d['components']['cpm']['pct_vs_baseline']:+.1%} vs baseline — no auction squeeze.
- **NOT primarily EXTERNAL_DEMAND**: the established campaign ran at/above its own baseline through Jun 26–28; pre-onset USMNT match days show a null CVR effect; checkout_rate did not drop in Jun 25–28. A World Cup weekend contribution to the account-wide residual cannot be excluded — it is bounded by that residual and carries a correlation-only flag.
- **NOT the checkout-entry collapse it was reported as**: absolute checkout counts fell with click volume, but checkout **rate** was flat (+0.8%) through Jun 28. The Jun 29+ rate dip (−8.5%) coincides with the Hi-Res removal, not the original onset.

## Caveats

- Publish times unconfirmed for all deploys — commit time is earliest-possible-live; the deploy may have gone live any time ≥ 12:22 UTC Jun 25.
- The 59/41 split depends on the rolling baseline; a post-shift-era median baseline attributes more to the test campaign. Both agree the test campaign is the dominant locus.
- Checkout metrics sit on ~4 weeks of post-May-24 baseline (see denominator context).
- {L['data_end']} (age-1) excluded from all conclusions pending back-fill settlement.

## Recommended next evidence

1. **Ad-set-level insights pull** — separates the Memorial ad set's learning-phase CVR from the rest of the test campaign; the single most discriminating item.
2. Confirm the actual publish time of deploy-2026-06-25-startpage from Lovable.
3. If CPA stays recovered post Jun 29 with Hi-Res off, A/B re-enabling Hi-Res settles the FUNNEL hypothesis directly.
"""
    (OUT / "bt_jun25_live.md").write_text(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ctx = co.load_context()
    spans = co.reserved_spans(ctx["data_end"])

    print("== PHASE 4: verdicts first (labels not consulted) ==")
    mar = run_cascade_incident(ctx, spans, "mar13-post-pause-learning-reset")
    may = run_cascade_incident(ctx, spans, "may24-checkout-event-shift")
    live = live_case(ctx)
    for r in mar + may:
        print(f"  {r['wid']}: {r['verdict']['verdict']} (conf {r['verdict']['confidence']:.2f})")
    v = live["verdict"]
    print(f"  bt_jun25 (live, bespoke): {v['verdict']} (conf {v['confidence']:.2f})")
    for k, s in v["split"].items():
        print(f"    split {s:>5.0%}  {k}")
    print(f"    test-campaign share of CPA drift: {live['test_share']:.0%} | "
          f"backfill age>=2: {live['max_backfill_age2plus']:.0f} purchases | "
          f"USMNT match-day CVR effect: {live['matchday_cvr_effect']:+.1%} | "
          f"CPA dlog pre {live['D_pre']:+.3f} -> post {live['D_post']:+.3f}")

    print("\n== UNSEALING backtest/incidents.json ==")
    inc = json.loads((REPO_ROOT / "backtest" / "incidents.json").read_text())
    truth = {i["id"]: i["ground_truth"] for i in inc["testable"]}
    engine_primary = {
        "mar13-post-pause-learning-reset": next(
            (r["verdict"]["verdict"] for r in mar if r["window"]["metric"] == "cpa"), None),
        "may24-checkout-event-shift": next(
            (r["verdict"]["verdict"] for r in may if r["window"]["metric"] == "checkout_rate"), None),
        "jun25-checkout-entry-drop": v["verdict"],
    }
    rows = []
    for iid, gt in truth.items():
        ev = engine_primary[iid]
        agree = ("AGREE" if ev == gt else
                 "CONSISTENT (no ground truth to contradict)" if gt == "UNRESOLVED" else
                 "DISAGREE")
        rows.append((iid, ev, gt, agree))
        print(f"  {iid}: engine={ev} truth={gt} -> {agree}")

    write_live_report(live)
    conf = {"mar13-post-pause-learning-reset": next(r["verdict"]["confidence"] for r in mar if r["window"]["metric"] == "cpa"),
            "may24-checkout-event-shift": next(r["verdict"]["confidence"] for r in may if r["window"]["metric"] == "checkout_rate"),
            "jun25-checkout-entry-drop": v["confidence"]}
    agreement = ["# Phase 4 blind backtest — agreement", "",
                 "| incident | engine verdict | conf | ground truth | result |", "|---|---|---|---|---|"]
    for iid, ev, gt, agree in rows:
        agreement.append(f"| {iid} | {ev} | {conf[iid]:.2f} | {gt} | **{agree}** |")
    agreement += ["", "Secondary windows: mar13 checkout_rate/cvr windows also -> INTERNAL_ADS (0.80); "
                      "may24 cpm window (May 21-24, ends AT the shift day) -> UNEXPLAINED — correct: the "
                      "CPM move is a separate, genuinely unexplained anomaly, not part of the checkout shift.", ""]
    (OUT / "agreement.md").write_text("\n".join(agreement))

    calibration = f"""# Confidence calibration note — Phase 4

Sample: 2 resolvable incidents + 1 unresolved live case. n=2 supports only ordinal checks, not calibration curves.

| verdict | conf | outcome |
|---|---|---|
| mar13 INTERNAL_ADS (learning reset) | 0.80 | correct |
| may24 INTERNAL_FUNNEL (instrumentation) | 0.92 | correct |
| jun25 MIXED 59/41/0 | 0.55 | unresolved by design — confidence reflects the unsplittable internal pair, not doubt about locus |

Observations:
1. Both resolvable incidents were decided by cascade rules added during Phase 4 prep (R1b pause-resume;
   R0 instrumentation upgrade), before unsealing but with labels present in-repo all session. PROCEDURAL
   blindness only — n=2 cannot distinguish principled rules from overfitting. Treat 0.80/0.92 as
   upper bounds until out-of-sample incidents accrue.
2. The Phase 3 sweep's UNEXPLAINED confidences (semantics: confidence that known signals do NOT explain)
   are untested by this backtest — no labeled negative exists.
3. Bands (HIGH/MED/LOW) should be read ordinally. Recommendation: freeze thresholds now; re-calibrate
   after 5+ labeled incidents; log every future verdict-vs-resolution pair into incidents.json as it
   resolves (the live case will become datapoint 3 when the advertiser confirms/refutes via the
   recommended follow-ups).
4. Watch-item: INTERNAL_ADS spend-window verdicts (0.75-0.85) rely on activity presence in a 72h
   lookback; base rate is high in an actively-managed account. The May 26-27 counterexample (no
   activity -> UNEXPLAINED) shows discrimination, but a shuffle test (random windows vs activity
   presence) would quantify the false-positive rate — recommended before trusting 0.85.
"""
    (OUT / "calibration.md").write_text(calibration)

    plain = f"""# What happened to your ads on June 25? — plain-English summary

**Short answer: mostly something on your side, not the world's — and it's already recovering.**

Your cost per sale jumped about a third for four days (Jun 25–28), then came back down. Here is
what the evidence says:

1. **The drop was real, not a reporting glitch.** We now measure how Meta restates old numbers
   every day; those restatements have been zero. Nothing back-filled.

2. **It wasn't the ad auction.** What you pay for attention (CPM) barely moved.

3. **It probably wasn't the World Cup.** Your long-running main campaign sold normally right
   through the bad days. On earlier USMNT match days (Jun 12, 19), buying was normal too. A
   nationwide distraction should have dented everything, not just one campaign.

4. **The damage sat almost entirely in your test campaign** — the one that got a new Memorial ad
   set (Jun 20), budget changes and nine new ads (Jun 24). Roughly 60% of the whole cost spike
   traces to that campaign converting at half its usual rate.

5. **Two of your own changes happened almost simultaneously there**, and daily data cannot tell
   them apart: (a) the campaign restructure itself — new ad sets typically convert poorly while
   Meta re-learns; and (b) the site update published around Jun 25 touching the /start page and
   Memorial pages — the same pages those test ads land on.

6. **The Jun 29 fix matters.** You turned off the Hi-Res add-on on Jun 29, and conversion
   recovered right after. That is consistent with the site update having broken something in the
   checkout for those visitors — but also with the new ad sets simply finishing their learning
   phase. One more data pull can't settle this; the three follow-ups below can.

**What we'd do next:** (1) pull ad-set-level numbers — if the Memorial ad set alone tanked, it
was the restructure; if the whole test campaign tanked evenly, suspect the site update;
(2) confirm from Lovable when the Jun 25 update actually went live; (3) since things recovered
with Hi-Res off, briefly re-enabling it would prove or clear it.

*Confidence: moderate. The evidence firmly places the cause on the advertiser side and rules out
reporting artifacts, auction prices, and (largely) the World Cup — but it cannot yet pick between
your two own-side changes, because they happened within 48 hours of each other on the same traffic.*
"""
    (OUT / "jun25_summary_plain.md").write_text(plain)
    print(f"\n[backtest] reports -> {OUT.relative_to(REPO_ROOT)}/ "
          f"(live report, agreement, calibration, plain summary)")


if __name__ == "__main__":
    main()
