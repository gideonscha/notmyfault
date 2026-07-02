# Anomaly Timeline — full account history (Phase 1: detection only)

Data: `data/meta/account_daily.csv`, 2025-11-20 .. 2026-07-01 (210 delivering days used).
Model: trailing-90d rolling baseline per metric, day-of-week adjusted, log-space robust (median/MAD); anomaly = |z| >= 2 for >= 2 consecutive days. No labeling or classification in this phase.

## Data-quality notes

- **Delivery pause excluded from all baselines: 2026-02-27 .. 2026-03-12** (account-level event `acct-delivery-pause-2026-02-27` in `signals/library.json`). Wider than the known 8-day data gap: Feb 27 - Mar 4 returned rows with zero spend/impressions, Mar 5 - 12 returned no rows. 2026-03-02 records 2 purchases against $0 spend — lagged attribution landing inside the pause.
- Warmup: baselines require >= 28 trailing days, so scoring starts 2025-12-18; 2025-11-20 .. 2025-12-17 is unscored.
- `checkouts_initiated` first appears 2026-01-25 and is missing Jan 29 - Feb 2, 2026 on days that otherwise delivered normally — likely a checkout-event tracking gap, worth remembering when the verdict engine reasons about checkout_rate (flagged here as data quality, not classified).
- **checkout_rate steps x~6.5 overnight on 2026-05-24** (47 -> 287 checkouts day-over-day on similar clicks) and persists — a structural level shift consistent with an event-definition/tracking change, not gradual demand movement (account-level event `acct-checkout-event-shift-2026-05-24` in `signals/library.json`, not classified here). The long checkout_rate 'high' window starting 2026-05-24 is this shift being absorbed by the trailing baseline; checkout_rate comparisons spanning the date are invalid without segmenting.
- Post-pause days (2026-03-13 onward) are scored normally but carry learning-phase risk; the first flags after the pause should be read with that in mind.

## Month-position diagnostics (NOT applied to z-scores)

~7.5 months of history gives each bucket only a handful of same-position weeks and confounds bucket effects with trend/season, so these factors are reported for orientation only and are deliberately not folded into the baselines. Revisit at 12+ months.

| metric | bucket | n days | factor vs overall median | approx SE |
|---|---|---|---|---|
| cpa | early(1-10) | 61 | 0.904 | ±0.056 |
| cpa | mid(11-20) | 69 | 0.999 | ±0.065 |
| cpa | late(21-31) | 80 | 1.037 | ±0.040 |
| cpm | early(1-10) | 61 | 0.990 | ±0.022 |
| cpm | mid(11-20) | 69 | 1.010 | ±0.015 |
| cpm | late(21-31) | 80 | 1.006 | ±0.021 |
| ctr | early(1-10) | 61 | 1.038 | ±0.026 |
| ctr | mid(11-20) | 69 | 0.978 | ±0.037 |
| ctr | late(21-31) | 80 | 0.972 | ±0.031 |
| cvr | early(1-10) | 61 | 0.929 | ±0.052 |
| cvr | mid(11-20) | 69 | 1.060 | ±0.037 |
| cvr | late(21-31) | 80 | 0.971 | ±0.027 |
| spend | early(1-10) | 61 | 1.090 | ±0.036 |
| spend | mid(11-20) | 69 | 1.008 | ±0.061 |
| spend | late(21-31) | 80 | 0.869 | ±0.051 |
| checkout_rate | early(1-10) | 39 | 1.016 | ±0.076 |
| checkout_rate | mid(11-20) | 48 | 0.888 | ±0.053 |
| checkout_rate | late(21-31) | 52 | 1.107 | ±0.094 |

## CPA anomaly windows (7)

### 2025-12-18 .. 2025-12-19 — CPA ▲ +58.9% vs baseline (2 days, mean z +5.0, peak z +7.2)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | -31.4% | -82% | 2 |
| CTR | -39.9% | 110% | 2 |
| CVR | -28.2% | 72% | 2 |
| _identity residual_ | dlog -0.000 | — | — |

### 2025-12-29 .. 2025-12-31 — CPA ▲ +63.4% vs baseline (3 days, mean z +3.7, peak z +5.6)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | -44.0% | -118% | 3 |
| CTR | -45.1% | 122% | 3 |
| CVR | -42.9% | 114% | 3 |
| _identity residual_ | dlog -0.088 | — | — |

### 2026-01-06 .. 2026-01-07 — CPA ▲ +136.9% vs baseline (2 days, mean z +4.9, peak z +5.2)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | -42.2% | -64% | 2 |
| CTR | -28.2% | 38% | 2 |
| CVR | -66.9% | 128% | 2 |
| _identity residual_ | dlog -0.028 | — | — |

### 2026-01-12 .. 2026-01-13 — CPA ▲ +68.3% vs baseline (2 days, mean z +2.4, peak z +2.7)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | -48.4% | -127% | 2 |
| CTR | -34.7% | 82% | 2 |
| CVR | -54.0% | 149% | 2 |
| _identity residual_ | dlog -0.019 | — | — |

### 2026-03-13 .. 2026-03-17 — CPA ▲ +174.7% vs baseline (5 days, mean z +3.3, peak z +4.4)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | +11.8% | 11% | 5 |
| CTR | -14.5% | 16% | 5 |
| CVR | -51.8% | 72% | 5 |
| _identity residual_ | dlog +0.012 | — | — |

### 2026-06-07 .. 2026-06-08 — CPA ▼ -39.2% vs baseline (2 days, mean z -2.0, peak z -2.1)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | +9.7% | -19% | 2 |
| CTR | +24.0% | 43% | 2 |
| CVR | +38.8% | 66% | 2 |
| _identity residual_ | dlog -0.046 | — | — |

### 2026-06-26 .. 2026-06-28 — CPA ▲ +59.1% vs baseline (3 days, mean z +2.1, peak z +2.1)

| component | vs own baseline | share of CPA drift | days used |
|---|---|---|---|
| CPM | +10.2% | 21% | 3 |
| CTR | -11.5% | 26% | 3 |
| CVR | -21.9% | 53% | 3 |
| _identity residual_ | dlog -0.002 | — | — |

## Other metric anomaly windows (22)

| metric | window | days | direction | vs baseline | mean z | peak z |
|---|---|---|---|---|---|---|
| cpm | 2025-12-19 .. 2025-12-20 | 2 | low | -45.1% | -2.3 | -2.3 |
| cvr | 2025-12-21 .. 2025-12-24 | 4 | low | -29.5% | -3.2 | -4.3 |
| cpm | 2025-12-23 .. 2025-12-27 | 5 | low | -50.3% | -2.2 | -2.4 |
| cvr | 2025-12-30 .. 2025-12-31 | 2 | low | -47.6% | -3.2 | -3.2 |
| cvr | 2026-01-06 .. 2026-01-07 | 2 | low | -66.9% | -3.8 | -4.2 |
| cvr | 2026-01-13 .. 2026-01-14 | 2 | low | -55.8% | -2.6 | -3.0 |
| checkout_rate | 2026-03-13 .. 2026-03-14 | 2 | low | -42.9% | -2.2 | -2.4 |
| cvr | 2026-03-13 .. 2026-03-16 | 4 | low | -55.4% | -2.9 | -4.0 |
| ctr | 2026-03-18 .. 2026-03-19 | 2 | low | -30.0% | -3.3 | -4.0 |
| cpm | 2026-03-20 .. 2026-03-22 | 3 | high | +44.0% | +2.8 | +3.0 |
| ctr | 2026-03-26 .. 2026-04-05 | 11 | low | -33.2% | -3.1 | -4.1 |
| spend | 2026-04-04 .. 2026-04-05 | 2 | high | +112.6% | +2.5 | +2.9 |
| spend | 2026-04-07 .. 2026-04-08 | 2 | high | +103.6% | +2.4 | +2.6 |
| checkout_rate | 2026-04-08 .. 2026-04-09 | 2 | high | +93.1% | +2.2 | +2.3 |
| ctr | 2026-04-10 .. 2026-04-11 | 2 | low | -37.5% | -2.3 | -2.3 |
| spend | 2026-04-13 .. 2026-04-16 | 4 | high | +90.7% | +2.4 | +2.9 |
| spend | 2026-04-19 .. 2026-04-21 | 3 | high | +78.3% | +2.5 | +2.8 |
| spend | 2026-05-19 .. 2026-05-20 | 2 | low | -49.7% | -2.2 | -2.3 |
| cpm | 2026-05-21 .. 2026-05-24 | 4 | high | +32.5% | +3.1 | +3.6 |
| checkout_rate | 2026-05-24 .. 2026-06-25 | 33 | high | +484.0% | +4.4 | +6.8 |
| spend | 2026-05-26 .. 2026-05-27 | 2 | low | -52.7% | -2.1 | -2.2 |
| cpm | 2026-06-04 .. 2026-06-05 | 2 | high | +23.1% | +2.3 | +2.7 |
