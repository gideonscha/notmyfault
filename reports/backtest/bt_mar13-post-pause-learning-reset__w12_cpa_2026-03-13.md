# bt_mar13-post-pause-learning-reset__w12_cpa_2026-03-13 — CPA ▲ +174.7% · 2026-03-13 .. 2026-03-17

**VERDICT: INTERNAL_ADS** (confidence 0.80 — HIGH)

Tags: LEARNING_RESET

acct-delivery-pause-2026-02-27: window begins within 3d of a multi-day delivery pause ending — resume re-enters ad sets into learning (advertiser action). Consistent with the CVR-dominated pattern of a learning reset; the resume action itself appears in the activity log.

## The numbers

- 5 consecutive days beyond ±2σ (mean z +3.3, peak z +4.4) vs the day-of-week-adjusted trailing-90d baseline
- drift: +174.7% vs baseline (dlog +1.011)
- CPA decomposition (share of drift): CPM +11.8% (11%), CTR -14.5% (16%), CVR -51.8% (72%)

## Evidence ledger

| evidence | type | relation | direction | quantified effect | explains |
|---|---|---|---|---|---|
| payday_15th | rule (EXTERNAL_DEMAND) | in-window | stimulative | +5.3% (n=6) | dlog +0.010 |
| tax_refund_season | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| acct-delivery-pause-2026-02-27 | event (ACCOUNT) | adjacent-before | suppressive | prior only (correlation only) | — |
| ext-cpi-2026-03-11 | event (EXTERNAL_DEMAND) | adjacent-before | suppressive | prior only (correlation only) | — |
| update_campaign_run_status ×1 (ASC - Magic Portraits) | account activity [status] | in-window, first 2026-03-13T16:11 | — | direct advertiser action | — |

## Attribution

- observed drift: dlog +1.011
- explained by coefficient-backed signals: dlog +0.010 (1%)
- **unexplained residual: dlog +1.000 (99% of drift)**

## What it is NOT

- **NOT REPORTING_ARTIFACT**: no measurement-shift event on this metric; window is 107d before data end, outside the 3d attribution-lag zone

## Caveats

- Thresholds are v1 heuristics pending Phase 4 backtest calibration.
- Baselines carry ~7.5 months of history; month-position effects are diagnostics only and not removed from z-scores.
