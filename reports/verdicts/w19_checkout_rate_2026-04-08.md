# w19_checkout_rate_2026-04-08 — CHECKOUT_RATE ▲ +93.1% · 2026-04-08 .. 2026-04-09

**VERDICT: UNEXPLAINED** (confidence 1.00 — HIGH)

coefficient-backed evidence explains only 0% of the drift; no direction-consistent signals in the library. Advertiser actions (bid, budget, status, structure, targeting) in the 72h before/at onset — INTERNAL_ADS candidate, unquantified (v1 has no effect model for non-spend metrics).

## The numbers

- 2 consecutive days beyond ±2σ (mean z +2.2, peak z +2.3) vs the day-of-week-adjusted trailing-90d baseline
- drift: +93.1% vs baseline (dlog +0.658)

## Evidence ledger

| evidence | type | relation | direction | quantified effect | explains |
|---|---|---|---|---|---|
| snap_window | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| tax_refund_season | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| ext-cpi-2026-04-10 | event (EXTERNAL_DEMAND) | adjacent-after | suppressive | prior only (direction-inconsistent) | — |
| update_ad_set_bid_strategy ×2 (ASC_MagicPortraits_FreeOffer) | account activity [bid] | pre-window, first 2026-04-06T22:58 | — | direct advertiser action | — |
| update_campaign_budget ×1 (ASC - Magic Portraits) | account activity [budget] | pre-window, first 2026-04-05T00:57 | — | direct advertiser action | — |
| update_campaign_budget_scheduling_state ×1 (ASC_MagicPortraits_FreeOffer) | account activity [budget] | pre-window, first 2026-04-06T23:43 | — | direct advertiser action | — |
| create_ad ×6 (MPC900EC_C1, MPC900EC_C2) | account activity [creative] | in-window, first 2026-04-09T15:17 | — | direct advertiser action | — |
| create_ad ×18 (MPC900EC_A9, MPC900EC_B5_EPK) | account activity [creative] | pre-window, first 2026-04-06T22:58 | — | direct advertiser action | — |
| update_ad_creative ×29 (MPC900EC_A5, MPC900EC_B7_EPK) | account activity [creative] | pre-window, first 2026-04-07T08:01 | — | direct advertiser action | — |
| update_ad_set_run_status ×5 (ASC_MagicPortraits_FreeOffer) | account activity [status] | pre-window, first 2026-04-06T22:59 | — | direct advertiser action | — |
| update_campaign_run_status ×4 (ASC - Magic Portraits, ASC_Magic Portraits_FreeOffer_Value) | account activity [status] | pre-window, first 2026-04-05T00:57 | — | direct advertiser action | — |
| create_ad_set ×2 (ASC_MagicPortraits_FreeOffer) | account activity [structure] | pre-window, first 2026-04-06T22:58 | — | direct advertiser action | — |
| create_campaign_group ×2 (ASC_Magic Portraits_FreeOffer_Value, ASC_Magic Portraits_FreeOffer) | account activity [structure] | pre-window, first 2026-04-06T22:58 | — | direct advertiser action | — |
| update_ad_set_optimization_goal ×2 (ASC_MagicPortraits_FreeOffer) | account activity [targeting] | pre-window, first 2026-04-06T22:58 | — | direct advertiser action | — |
| update_ad_set_target_spec ×2 (ASC_MagicPortraits_FreeOffer) | account activity [targeting] | pre-window, first 2026-04-06T22:58 | — | direct advertiser action | — |

## Attribution

- observed drift: dlog +0.658
- explained by coefficient-backed signals: dlog +0.000 (0%)
- **unexplained residual: dlog +0.658 (100% of drift)**

## What it is NOT

- **NOT REPORTING_ARTIFACT**: no measurement-shift event on this metric; window is 84d before data end, outside the 3d attribution-lag zone
- **NOT INTERNAL_FUNNEL**: no site deploys recorded in-window or in the preceding 72h — CAVEAT: the deploy timeline is a curated extract, not exhaustive; weak rejection
- **NOT EXTERNAL_DEMAND**: ext-cpi-2026-04-10 overlaps but its direction (suppressive) is inconsistent with the observed drift

## Caveats

- Thresholds are v1 heuristics pending Phase 4 backtest calibration.
- Baselines carry ~7.5 months of history; month-position effects are diagnostics only and not removed from z-scores.
