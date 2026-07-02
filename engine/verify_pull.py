"""Phase 0 verification — row counts, date coverage, gaps, sample rows.

Usage: python -m engine.verify_pull
Prints a verification report for every file in data/meta/. Exits non-zero if
any expected pull is missing or has date gaps beyond tolerance.
"""

from __future__ import annotations

import sys

import pandas as pd

from engine.config import DATA_META
from engine.fetch_meta import PULLS


def verify_one(name: str) -> bool:
    path = DATA_META / f"{name}.csv"
    if not path.exists():
        print(f"[{name}] MISSING — run: python -m engine.fetch_meta --only {name}")
        return False
    df = pd.read_csv(path, parse_dates=["date_start"])
    days = df["date_start"].dt.date
    span = pd.date_range(days.min(), days.max(), freq="D").date
    missing = sorted(set(span) - set(days))
    print(f"\n[{name}] {len(df)} rows | {days.min()} .. {days.max()} "
          f"({days.nunique()} distinct days, {len(missing)} missing in span)")
    if missing:
        head = ", ".join(str(d) for d in missing[:10])
        print(f"  missing days: {head}{' ...' if len(missing) > 10 else ''}")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        cols = [c for c in ("date_start", "campaign_name", "publisher_platform",
                            "platform_position", "age", "gender", "spend", "impressions",
                            "cpm", "ctr", "inline_link_clicks", "purchases", "cpa", "cvr")
                if c in df.columns]
        print(df[cols].head(3).to_string(index=False))
        print("  ...")
        print(df[cols].tail(3).to_string(index=False))
    if "spend" in df.columns:
        total = df["spend"].sum()
        print(f"  total spend in range: {total:,.2f}")
    # Account-level pulls should have few gaps; zero-delivery days are legal
    # so gaps are reported, not fatal, unless coverage is very thin.
    return days.nunique() >= 0.5 * len(span)


def main() -> None:
    ok = all([verify_one(name) for name in PULLS])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
