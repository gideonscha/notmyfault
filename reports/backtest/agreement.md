# Phase 4 blind backtest — agreement

| incident | engine verdict | conf | ground truth | result |
|---|---|---|---|---|
| mar13-post-pause-learning-reset | INTERNAL_ADS | 0.80 | INTERNAL_ADS | **AGREE** |
| may24-checkout-event-shift | INTERNAL_FUNNEL | 0.92 | INTERNAL_FUNNEL | **AGREE** |
| jun25-checkout-entry-drop | MIXED | 0.55 | UNRESOLVED | **CONSISTENT (no ground truth to contradict)** |

Secondary windows: mar13 checkout_rate/cvr windows also -> INTERNAL_ADS (0.80); may24 cpm window (May 21-24, ends AT the shift day) -> UNEXPLAINED — correct: the CPM move is a separate, genuinely unexplained anomaly, not part of the checkout shift.
