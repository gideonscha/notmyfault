# bt_may24-checkout-event-shift__w24_cpm_2026-05-21 — CPM ▲ +32.5% · 2026-05-21 .. 2026-05-24

**VERDICT: UNEXPLAINED** (confidence 1.00 — HIGH)

Tags: REACTIVE_ACTION

coefficient-backed evidence explains only 0% of the drift; 1 direction-consistent event(s) overlap but are prior-only (correlation only, coefficient unknown) and are NOT stretched to cover the residual. Advertiser actions (budget) in the 72h before/at onset — INTERNAL_ADS candidate, unquantified (v1 has no effect model for non-spend metrics).

## The numbers

- 4 consecutive days beyond ±2σ (mean z +3.1, peak z +3.6) vs the day-of-week-adjusted trailing-90d baseline
- drift: +32.5% vs baseline (dlog +0.281)

## Evidence ledger

| evidence | type | relation | direction | quantified effect | explains |
|---|---|---|---|---|---|
| acct-checkout-event-shift-2026-05-24 | event (ACCOUNT) | overlap | mixed | prior only (correlation only) | — |
| update_ad_set_budget ×3 (ASC_TESTCAMPAIGN_HUMANS, ASC_TESTCAMPAIGN_MAGICPORTRAITS) | account activity [budget] | in-window, first 2026-05-21T08:52 | — | direct advertiser action | — |
| update_ad_set_budget ×2 (ASC_TESTCAMPAIGN_MAGICPORTRAITS) | account activity [budget] | pre-window, first 2026-05-19T13:25 | — | direct advertiser action | — |
| create_ad ×8 (MPC900EC_F1, MPC900EC_F2) | account activity [creative] | in-window, first 2026-05-21T13:52 | — | direct advertiser action | — |
| create_ad ×6 (MPC900EC_A10, MPC900EC_A11) | account activity [creative] | pre-window, first 2026-05-19T13:08 | — | direct advertiser action | — |
| update_ad_creative ×5 (MPC900EC_A2, MPC900EC_A1) | account activity [creative] | pre-window, first 2026-05-19T11:05 | — | direct advertiser action | — |
| deploy-2026-05-24-tracking (5 commits) | site deploy [INTERNAL_FUNNEL] | post-onset 2026-05-24 | — | earliest-possible-live, publish unconfirmed | — |

## Attribution

- observed drift: dlog +0.281
- explained by coefficient-backed signals: dlog +0.000 (0%)
- **unexplained residual: dlog +0.281 (100% of drift)**

## What it is NOT

- **NOT REPORTING_ARTIFACT**: no measurement-shift event on this metric; window is 39d before data end, outside the 3d attribution-lag zone
- **NOT INTERNAL_FUNNEL (via post-onset deploy)**: deploy-2026-05-24-tracking deployed after onset — response/tail-shaping, not an onset cause

## Caveats

- Thresholds are v1 heuristics pending Phase 4 backtest calibration.
- Baselines carry ~7.5 months of history; month-position effects are diagnostics only and not removed from z-scores.
