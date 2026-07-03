# bt_jun25_live — the Jun 25+ case · assessment through 2026-07-02

**VERDICT: MIXED** (confidence 0.55 — MEDIUM) · Tags: LIVE_CASE, REACTIVE_ACTION (Jun 29 Hi-Res disable)

The Jun 25-28 CPA drift is quantifiably concentrated in the restructured test campaign; within that campaign the advertiser's own restructure (new Memorial ad set Jun 20, budget re-allocations and 9 new creatives Jun 24) and the Jun 25 /start+Memorial deploy burst fire within 48h of each other on the same traffic — daily-grain data cannot separate them. The demand environment (World Cup peak week, USMNT prime-time loss Jun 25, post-Father's-Day trough) is present but quantifiably weak here: the established campaign ran at/above its own baseline through the window, pre-onset USMNT match days show a null CVR effect (n=2), and checkout_rate did not drop in Jun 25-28. Attribution lag is quantifiably zero for days aged >= 2.

## Quantified split (Jun 25–28 CPA drift, dlog +0.286 = +33.2% vs baseline)

| component | share | basis |
|---|---|---|
| INTERNAL, test-campaign scoped (ADS restructure ∥ FUNNEL deploy) | 59% | counterfactual: test campaign at its own post-shift baseline CVR removes this much of the account drift |
| account-wide residual (WC weekend demand [prior-only] / Jun 19 budget +20% [INTERNAL_ADS]) | 41% | remainder; main campaign CPA mildly elevated on higher spend |
| REPORTING_ARTIFACT (attribution lag) | 0% | measured lag curve: max back-fill at age ≥2 = 0 purchases across 13 day-pairs |

**The INTERNAL 59% cannot be split between INTERNAL_ADS and INTERNAL_FUNNEL with daily data**: the restructure (Jun 20–24) and the deploy (Jun 25, earliest-possible-live 12:22 UTC, publish unconfirmed) act on the same traffic within 48h. Ad-set-level insights (not yet pulled) are the discriminating follow-up.

## Segments (per the Hi-Res note)

| segment | CPA vs baseline (dlog) | CVR | checkout_rate | note |
|---|---|---|---|---|
| Jun 25–28 (pre Hi-Res disable) | +0.286 (+33.2%) | test campaign 0.0105 vs own baseline 0.0216 (−51%); main 0.0294 vs 0.0353 (at/above) | 0.358 vs baseline 0.355 (**no drop**) | damage concentrated Jun 26–28; Jun 25 itself was fine (CVR 0.036) |
| Jun 29–2026-07-02 (post) | +0.128 (+13.6%) | recovered | 0.325 (−8% vs baseline) | recovery follows the Jun 29 11:45 UTC Hi-Res disable; checkout_rate dip matches the predicted composition shift (~80% attach incl. abandons). 2026-07-02 is age-1 and unsettled — excluded from conclusions |

## Decomposition (Jun 25–28, share of CPA drift)

- CPM: +12.8% vs own baseline (42% of drift)
- CTR: -10.2% vs own baseline (38% of drift)
- CVR: -9.6% vs own baseline (35% of drift)
- identity residual: dlog -0.043

CVR-dominant, CPM near-flat → **NOT EXTERNAL_AUCTION** (auction prices did not move against the account).

## Evidence ledger

| evidence | type | timing | weight in this verdict |
|---|---|---|---|
| ASC_TESTCAMPAIGN restructure: Memorial ad set created Jun 20 23:21, budgets re-cut Jun 24 (MEMORIAL $200→$300/d, HUMANS $250→$150/d), 9 new creatives Jun 24 | account activity (INTERNAL_ADS) | 1–5d pre-onset | primary internal candidate |
| deploy-2026-06-25-startpage: 7 commits 12:22–17:34 UTC on /start + Memorial (earliest-possible-live; publish unconfirmed) | SITE_DEPLOY (INTERNAL_FUNNEL) | onset-day | primary internal candidate — thematically linked to the Memorial ad set (MugBanner→Memorial) |
| update_campaign_budget Jun 19 10:23: main campaign $1,000→$1,200/day (+20%) | account activity (INTERNAL_ADS) | 6d pre-onset | account-wide residual candidate (spend +38% through window) |
| worldcup-2026-tournament (Jun 11–Jul 19) | event, EXTERNAL_DEMAND, suppressive | overlap, 4/4 pre-segment days (day-weight 1.0) | prior-only; weakened by main-campaign stability |
| worldcup-2026-usmnt-matchdays: Jun 25 (L 3–2 Türkiye, 10PM ET), Jul 1 (W 2–0 Bosnia) | event, EXTERNAL_DEMAND, suppressive | Jun 25 = 1/4 pre days (day-weight 0.25); Jul 1 in post | prior-only; **pre-onset match days Jun 12/19 show CVR effect -0.1% (n=2, null)** |
| fathers-day-2026 post-gifting cliff (Jun 22+) | event mechanism, EXTERNAL_DEMAND | window ended Jun 21; cliff unbounded | prior-only; Jun 22–24 CVR (0.029–0.031) shows no pre-onset trough |
| reactive-2026-06-29-hires-flag: Hi-Res add-on disabled 11:45 UTC | SITE_DEPLOY (REACTIVE_ACTION) | post-onset | not a cause; corroborates the anomaly was real and noticed; defines the segment split |
| May 24 denominator context (acct-checkout-event-shift) | ACCOUNT event | pre-existing | checkout metrics are measured in the post-May-24 attribution scope with only ~4wk of baseline — wide uncertainty on checkout comparisons |
| attribution-lag curve (backfill_observations/deltas.csv) | REPORTING check | — | zero back-fill at ages 2–14 across 13 day-pairs → lag explains 0% of Jun 25–30 drift; age-1 day excluded |

## What it is NOT

- **NOT REPORTING_ARTIFACT** (for days aged ≥2): measured back-fill is zero; the drop is real.
- **NOT EXTERNAL_AUCTION**: CPM +12.8% vs baseline — no auction squeeze.
- **NOT primarily EXTERNAL_DEMAND**: the established campaign ran at/above its own baseline through Jun 26–28; pre-onset USMNT match days show a null CVR effect; checkout_rate did not drop in Jun 25–28. A World Cup weekend contribution to the account-wide residual cannot be excluded — it is bounded by that residual and carries a correlation-only flag.
- **NOT the checkout-entry collapse it was reported as**: absolute checkout counts fell with click volume, but checkout **rate** was flat (+0.8%) through Jun 28. The Jun 29+ rate dip (−8.5%) coincides with the Hi-Res removal, not the original onset.

## Caveats

- Publish times unconfirmed for all deploys — commit time is earliest-possible-live; the deploy may have gone live any time ≥ 12:22 UTC Jun 25.
- The 59/41 split depends on the rolling baseline; a post-shift-era median baseline attributes more to the test campaign. Both agree the test campaign is the dominant locus.
- Checkout metrics sit on ~4 weeks of post-May-24 baseline (see denominator context).
- 2026-07-02 (age-1) excluded from all conclusions pending back-fill settlement.

## Recommended next evidence

1. **Ad-set-level insights pull** — separates the Memorial ad set's learning-phase CVR from the rest of the test campaign; the single most discriminating item.
2. Confirm the actual publish time of deploy-2026-06-25-startpage from Lovable.
3. If CPA stays recovered post Jun 29 with Hi-Res off, A/B re-enabling Hi-Res settles the FUNNEL hypothesis directly.
