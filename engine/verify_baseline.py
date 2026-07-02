"""Verify account_daily against the frozen local Phase 0 baseline.

The first Phase 0 pull ran locally on 2026-07-02 and its per-day files were
never committed; only these aggregates survive, frozen here as ground truth
for every re-pull:

    216 rows | coverage 2025-11-20 .. 2026-07-01
    zero-delivery gap 2026-03-05 .. 2026-03-12 (8 days)
    total spend 368,070.58

Spend micro-restates for a short period post-close: the 2026-07-02 16:46 UTC
re-pull of the identical range returned 368,070.99 — +$0.41 vs the local pull
~7h earlier (recorded in data/meta/backfill_observations/). So the spend check
uses a small absolute tolerance; it exists to catch structural errors (wrong
account, wrong attribution settings, duplicated rows — all $100s+ deltas),
not cent-level reconciliation. Purchases on the trailing ~7 days of the
window are EXPECTED to drift upward as attribution back-fills — that drift is
signal, not error (see engine/snapshot_backfill.py), and is not checked here.
Per-day deltas against the local baseline are not computable because the
local per-day files were never committed; snapshots from this day forward
close that gap.

Usage: python -m engine.verify_baseline    # exits non-zero on mismatch
"""

from __future__ import annotations

import datetime as dt
import sys

import pandas as pd

from engine.config import DATA_META

BASELINE = {
    "window": (dt.date(2025, 11, 20), dt.date(2026, 7, 1)),
    "rows": 216,
    "gap": (dt.date(2026, 3, 5), dt.date(2026, 3, 12)),
    "total_spend": 368_070.58,
    "pulled_locally": dt.date(2026, 7, 2),
}
SPEND_TOLERANCE = 5.00  # post-close reconciliation is cents; structural errors are $100s+


def main() -> None:
    path = DATA_META / "account_daily.csv"
    if not path.exists():
        sys.exit(f"{path} missing — run: python -m engine.fetch_meta --only account_daily")
    df = pd.read_csv(path, parse_dates=["date_start"])
    lo, hi = BASELINE["window"]
    win = df[(df["date_start"].dt.date >= lo) & (df["date_start"].dt.date <= hi)]
    days = set(win["date_start"].dt.date)

    gap_lo, gap_hi = BASELINE["gap"]
    expected_gap = {gap_lo + dt.timedelta(days=i) for i in range((gap_hi - gap_lo).days + 1)}
    span = set(pd.date_range(lo, hi, freq="D").date)
    missing = span - days

    spend = round(win["spend"].sum(), 2)
    checks = [
        ("rows in window", len(win), BASELINE["rows"], len(win) == BASELINE["rows"]),
        ("coverage start", days and min(days), lo, bool(days) and min(days) == lo),
        ("coverage end", days and max(days), hi, bool(days) and max(days) == hi),
        ("missing days == known gap", sorted(missing), sorted(expected_gap), missing == expected_gap),
        (f"total spend in window (±{SPEND_TOLERANCE:.2f}, delta {spend - BASELINE['total_spend']:+.2f})",
         spend, BASELINE["total_spend"], abs(spend - BASELINE["total_spend"]) <= SPEND_TOLERANCE),
    ]
    ok = True
    print(f"[verify_baseline] account_daily vs local Phase 0 baseline (pulled {BASELINE['pulled_locally']})")
    for label, got, want, passed in checks:
        ok &= passed
        print(f"  {'PASS' if passed else 'FAIL'}  {label}: got {got!r}, expected {want!r}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
