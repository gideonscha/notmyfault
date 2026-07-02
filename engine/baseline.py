"""Phase 1 — self-baseline model (brief §5). NOT YET IMPLEMENTED.

Planned: trailing 90-day rolling baseline per metric (CPA, CPM, CTR, CVR,
checkout-entry rate, spend), adjusted for day-of-week and month-position
effects from the account's own 12-month history. Anomaly = metric beyond
±2σ of adjusted baseline for >=2 consecutive days (tunable). Also computes
per-signal historical response coefficients enabling quantified MIXED verdicts.
"""

raise NotImplementedError("Phase 1 — implement after Phase 0 data pull is verified")
