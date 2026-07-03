# bt_mar13-post-pause-learning-reset__w11_checkout_rate_2026-03-13 — CHECKOUT_RATE ▼ -42.9% · 2026-03-13 .. 2026-03-14

**VERDICT: INTERNAL_ADS** (confidence 0.80 — HIGH)

Tags: LEARNING_RESET

acct-delivery-pause-2026-02-27: window begins within 3d of a multi-day delivery pause ending — resume re-enters ad sets into learning (advertiser action). Consistent with the CVR-dominated pattern of a learning reset; the resume action itself appears in the activity log.

## The numbers

- 2 consecutive days beyond ±2σ (mean z -2.2, peak z -2.4) vs the day-of-week-adjusted trailing-90d baseline
- drift: -42.9% vs baseline (dlog -0.561)

## Evidence ledger

| evidence | type | relation | direction | quantified effect | explains |
|---|---|---|---|---|---|
| tax_refund_season | rule (EXTERNAL_DEMAND) | in-window | stimulative | prior only | — |
| acct-delivery-pause-2026-02-27 | event (ACCOUNT) | adjacent-before | suppressive | prior only (correlation only) | — |
| ext-cpi-2026-03-11 | event (EXTERNAL_DEMAND) | adjacent-before | suppressive | prior only (correlation only) | — |
| update_campaign_run_status ×1 (ASC - Magic Portraits) | account activity [status] | in-window, first 2026-03-13T16:11 | — | direct advertiser action | — |

## Attribution

- observed drift: dlog -0.561
- explained by coefficient-backed signals: dlog -0.000 (0%)
- **unexplained residual: dlog -0.561 (100% of drift)**

## What it is NOT

- **NOT REPORTING_ARTIFACT**: no measurement-shift event on this metric; window is 110d before data end, outside the 3d attribution-lag zone

## Caveats

- Thresholds are v1 heuristics pending Phase 4 backtest calibration.
- Baselines carry ~7.5 months of history; month-position effects are diagnostics only and not removed from z-scores.
