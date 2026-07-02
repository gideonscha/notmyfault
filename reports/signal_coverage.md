# Signal Coverage — Phase 1 anomaly windows x signal library (no verdicts)

29 anomaly windows (engine/baseline.py, |z| >= 2 x >= 2d) joined against 15 dated signals and 8 recurring rules. Events marked *adjacent* start within ±2 days of the window. Rule coefficients are account-specific median log-residual effects (engine/rules.py); 'prior only' = fewer than 4 occurrences, coefficient unknown (anti-horoscope rule). Classification is deliberately absent — Phase 3.

NOTE: signals/library.json carries `_pending`: the library_seed.json attachment did not reach the container; this report regenerates in seconds once the seed is merged (`python -m engine.coverage`).

| # | window | metric | dir | vs baseline | overlapping events | adjacent events | rule flags (coef for window metric) |
|---|---|---|---|---|---|---|---|
| 1 | 2025-12-18 .. 2025-12-19 | cpa | high | +58.9% | ext-cpi-2025-12-18; meta-glitchmas-bfcm-2025 | — | cpi_release (+13.8%) |
| 2 | 2025-12-19 .. 2025-12-20 | cpm | low | -45.1% | meta-glitchmas-bfcm-2025 | ext-cpi-2025-12-18 | — |
| 3 | 2025-12-21 .. 2025-12-24 | cvr | low | -29.5% | — | meta-glitchmas-bfcm-2025 | — |
| 4 | 2025-12-23 .. 2025-12-27 | cpm | low | -50.3% | — | — | federal_holiday (-20.8%) |
| 5 | 2025-12-29 .. 2025-12-31 | cpa | high | +63.4% | — | — | month_end (+30.0%) |
| 6 | 2025-12-30 .. 2025-12-31 | cvr | low | -47.6% | — | — | month_end (-29.6%) |
| 7 | 2026-01-06 .. 2026-01-07 | cpa | high | +136.9% | — | meta-ads-delivery-outage-2026-01-08 | snap_window (+6.6%) |
| 8 | 2026-01-06 .. 2026-01-07 | cvr | low | -66.9% | — | meta-ads-delivery-outage-2026-01-08 | snap_window (-10.7%) |
| 9 | 2026-01-12 .. 2026-01-13 | cpa | high | +68.3% | ext-cpi-2026-01-13 | — | cpi_release (+13.8%) |
| 10 | 2026-01-13 .. 2026-01-14 | cvr | low | -55.8% | ext-cpi-2026-01-13 | — | cpi_release (+5.3%) |
| 11 | 2026-03-13 .. 2026-03-14 | checkout_rate | low | -42.9% | — | acct-delivery-pause-2026-02-27; ext-cpi-2026-03-11 | tax_refund_season (prior only) |
| 12 | 2026-03-13 .. 2026-03-17 | cpa | high | +174.7% | — | acct-delivery-pause-2026-02-27; ext-cpi-2026-03-11 | payday_15th (+5.3%); tax_refund_season (prior only) |
| 13 | 2026-03-13 .. 2026-03-16 | cvr | low | -55.4% | — | acct-delivery-pause-2026-02-27; ext-cpi-2026-03-11 | payday_15th (-11.1%); tax_refund_season (prior only) |
| 14 | 2026-03-18 .. 2026-03-19 | ctr | low | -30.0% | — | — | tax_refund_season (prior only) |
| 15 | 2026-03-20 .. 2026-03-22 | cpm | high | +44.0% | — | — | tax_refund_season (prior only) |
| 16 | 2026-03-26 .. 2026-04-05 | ctr | low | -33.2% | — | — | month_end (-13.7%); payday_1st (-17.7%); snap_window (-20.2%); tax_refund_season (prior only) |
| 17 | 2026-04-04 .. 2026-04-05 | spend | high | +112.6% | — | — | snap_window (+15.0%); tax_refund_season (prior only) |
| 18 | 2026-04-07 .. 2026-04-08 | spend | high | +103.6% | — | ext-cpi-2026-04-10 | snap_window (+15.0%); tax_refund_season (prior only) |
| 19 | 2026-04-08 .. 2026-04-09 | checkout_rate | high | +93.1% | — | ext-cpi-2026-04-10 | snap_window (no coef for checkout_rate); tax_refund_season (prior only) |
| 20 | 2026-04-10 .. 2026-04-11 | ctr | low | -37.5% | ext-cpi-2026-04-10 | — | cpi_release (-13.6%); snap_window (-20.2%); tax_refund_season (prior only) |
| 21 | 2026-04-13 .. 2026-04-16 | spend | high | +90.7% | — | — | payday_15th (-23.2%); tax_refund_season (prior only) |
| 22 | 2026-04-19 .. 2026-04-21 | spend | high | +78.3% | — | — | — |
| 23 | 2026-05-19 .. 2026-05-20 | spend | low | -49.7% | — | — | — |
| 24 | 2026-05-21 .. 2026-05-24 | cpm | high | +32.5% | acct-checkout-event-shift-2026-05-24 | — | — |
| 25 | 2026-05-24 .. 2026-06-25 | checkout_rate | high | +484.0% | acct-checkout-event-shift-2026-05-24; ext-cpi-2026-06-10; worldcup-2026-tournament | — | cpi_release (no coef for checkout_rate); federal_holiday (no coef for checkout_rate); month_end (no coef for checkout_rate); payday_15th (no coef for checkout_rate); payday_1st (no coef for checkout_rate); snap_window (no coef for checkout_rate) |
| 26 | 2026-05-26 .. 2026-05-27 | spend | low | -52.7% | acct-checkout-event-shift-2026-05-24 | — | — |
| 27 | 2026-06-04 .. 2026-06-05 | cpm | high | +23.1% | acct-checkout-event-shift-2026-05-24 | — | snap_window (-2.2%) |
| 28 | 2026-06-07 .. 2026-06-08 | cpa | low | -39.2% | acct-checkout-event-shift-2026-05-24 | ext-cpi-2026-06-10 | snap_window (+6.6%) |
| 29 | 2026-06-26 .. 2026-06-28 | cpa | high | +59.1% | acct-checkout-event-shift-2026-05-24; worldcup-2026-tournament | — | — |

## Windows with no dated-event coverage (10)

Anomalies explained (if at all) only by recurring rules or by nothing in the library yet — the priority list for library expansion (and the honest 'unexplained' pool Phase 3 must be willing to leave unexplained):

- #4 cpm low 2025-12-23 .. 2025-12-27 (-50.3%)
- #5 cpa high 2025-12-29 .. 2025-12-31 (+63.4%)
- #6 cvr low 2025-12-30 .. 2025-12-31 (-47.6%)
- #14 ctr low 2026-03-18 .. 2026-03-19 (-30.0%)
- #15 cpm high 2026-03-20 .. 2026-03-22 (+44.0%)
- #16 ctr low 2026-03-26 .. 2026-04-05 (-33.2%)
- #17 spend high 2026-04-04 .. 2026-04-05 (+112.6%)
- #21 spend high 2026-04-13 .. 2026-04-16 (+90.7%)
- #22 spend high 2026-04-19 .. 2026-04-21 (+78.3%)
- #23 spend low 2026-05-19 .. 2026-05-20 (-49.7%)
