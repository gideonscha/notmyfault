# bt_may24-checkout-event-shift__w25_checkout_rate_2026-05-24 — CHECKOUT_RATE ▲ +484.0% · 2026-05-24 .. 2026-06-25

**VERDICT: INTERNAL_FUNNEL** (confidence 0.92 — HIGH)

Tags: INSTRUMENTATION

acct-checkout-event-shift-2026-05-24: metric definition shifted, and the cause is evidenced — deploy-2026-05-24-tracking (site-side tracking change, mechanism VERIFIED by the mirrored-step check: the level change is attribution-scope, not behavior). Instrumentation subtype: manifests as a reporting artifact; the causal layer is the advertiser's site.

## The numbers

- 33 consecutive days beyond ±2σ (mean z +4.4, peak z +6.8) vs the day-of-week-adjusted trailing-90d baseline
- drift: +484.0% vs baseline (dlog +1.765)

## Evidence ledger

| evidence | type | relation | direction | quantified effect | explains |
|---|---|---|---|---|---|
| cpi_release | rule (EXTERNAL_DEMAND) | in-window | suppressive | prior only | — |
| federal_holiday | rule (EXTERNAL_DEMAND) | in-window | mixed | prior only | — |
| month_end | rule (EXTERNAL_DEMAND) | in-window | suppressive | prior only | — |
| payday_15th | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| payday_1st | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| snap_window | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| acct-checkout-event-shift-2026-05-24 | event (ACCOUNT) | overlap | mixed | prior only (correlation only) | — |
| ext-cpi-2026-06-10 | event (EXTERNAL_DEMAND) | overlap | suppressive | prior only (direction-inconsistent) | — |
| worldcup-2026-tournament | event (EXTERNAL_DEMAND) | overlap | suppressive | prior only (direction-inconsistent) | — |
| worldcup-2026-usmnt-matchdays | event (EXTERNAL_DEMAND) | overlap | suppressive | prior only (direction-inconsistent) | — |
| fathers-day-2026 | event (EXTERNAL_DEMAND) | overlap | stimulative | prior only (correlation only) | — |
| update_ad_set_bid_strategy ×3 (ASC_TESTCAMPAIGN_FREEMUGSPECIAL, ASC_TESTCAMPAIGN_PEELANDSTICK) | account activity [bid] | in-window, first 2026-05-28T12:13 | — | direct advertiser action | — |
| ad_account_update_spend_limit ×1 (Magic Pets) | account activity [budget] | in-window, first 2026-06-01T07:06 | — | direct advertiser action | — |
| update_ad_set_budget ×6 (ASC_TESTCAMPAIGN_MAGICPORTRAITS, ASC_TESTCAMPAIGN_FREEMUGSPECIAL) | account activity [budget] | in-window, first 2026-05-31T21:33 | — | direct advertiser action | — |
| update_ad_set_budget ×3 (ASC_TESTCAMPAIGN_HUMANS, ASC_TESTCAMPAIGN_MAGICPORTRAITS) | account activity [budget] | pre-window, first 2026-05-21T08:52 | — | direct advertiser action | — |
| update_campaign_budget ×1 (ASC - Magic Portraits) | account activity [budget] | in-window, first 2026-06-19T10:23 | — | direct advertiser action | — |
| update_campaign_budget_scheduling_state ×1 (ASC_TESTCAMPAIGN_PEELANDSTICK) | account activity [budget] | in-window, first 2026-06-01T22:45 | — | direct advertiser action | — |
| create_ad ×38 (MP_LS_Bed_Frenchie_v1, MP_LS_Chef_TabbyCat_v1) | account activity [creative] | in-window, first 2026-05-28T12:13 | — | direct advertiser action | — |
| create_ad ×8 (MPC900EC_F1, MPC900EC_F2) | account activity [creative] | pre-window, first 2026-05-21T13:52 | — | direct advertiser action | — |
| update_ad_creative ×69 (MPC900EC_E7, MPC900EC_F1) | account activity [creative] | in-window, first 2026-05-26T14:26 | — | direct advertiser action | — |
| update_ad_set_run_status ×7 (ASC_TESTCAMPAIGN_FREEMUGSPECIAL, ASC_TESTCAMPAIGN_PEELANDSTICK) | account activity [status] | in-window, first 2026-05-28T12:14 | — | direct advertiser action | — |
| update_campaign_run_status ×2 (ASC - Magic Portraits) | account activity [status] | in-window, first 2026-06-19T10:23 | — | direct advertiser action | — |
| create_ad_set ×3 (ASC_TESTCAMPAIGN_FREEMUGSPECIAL, ASC_TESTCAMPAIGN_PEELANDSTICK) | account activity [structure] | in-window, first 2026-05-28T12:13 | — | direct advertiser action | — |
| update_ad_set_optimization_goal ×3 (ASC_TESTCAMPAIGN_FREEMUGSPECIAL, ASC_TESTCAMPAIGN_PEELANDSTICK) | account activity [targeting] | in-window, first 2026-05-28T12:13 | — | direct advertiser action | — |
| update_ad_set_target_spec ×3 (ASC_TESTCAMPAIGN_FREEMUGSPECIAL, ASC_TESTCAMPAIGN_PEELANDSTICK) | account activity [targeting] | in-window, first 2026-05-28T12:13 | — | direct advertiser action | — |
| deploy-2026-05-24-tracking (5 commits) | site deploy [INTERNAL_FUNNEL] | onset-day 2026-05-24 | — | earliest-possible-live, publish unconfirmed | — |
| deploy-2026-06-25-startpage (7 commits) | site deploy [INTERNAL_FUNNEL] | post-onset 2026-06-25 | — | earliest-possible-live, publish unconfirmed | — |

## Attribution

- observed drift: dlog +1.765
- explained by coefficient-backed signals: dlog +0.000 (0%)
- **unexplained residual: dlog +1.765 (100% of drift)**

## What it is NOT

- (no candidate hypotheses were rejected)

## Caveats

- Thresholds are v1 heuristics pending Phase 4 backtest calibration.
- Baselines carry ~7.5 months of history; month-position effects are diagnostics only and not removed from z-scores.
- One or more matched events have LOW boundary confidence (window edges are conventional, not measured).
