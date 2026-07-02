"""Dated snapshots of the trailing attribution window — lag-curve raw data.

Meta restates conversions for roughly a week after the fact (attribution
back-fill). Each run copies the trailing N days of account_daily into
data/meta/backfill_observations/account_daily_asof_<DATE>.csv, then diffs the
overlapping days against the most recent prior snapshot and appends the
per-day deltas to data/meta/backfill_observations/deltas.csv:

    date_start, prev_asof, curr_asof, age_days (curr_asof - date_start),
    purchases_prev/curr/delta, purchase_value_prev/curr/delta,
    spend_prev/curr/delta

Accumulated over daily runs, deltas.csv IS the account's empirical
attribution-lag curve: how much a day's purchases grow at age 1, 2, ... N.
REPORTING_ARTIFACT verdicts (the cheapest class — check first) are scored
against this curve in Phase 1+.

Usage: python -m engine.snapshot_backfill [--window 14] [--asof YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

import pandas as pd

from engine.config import DATA_META

OBS_DIR = DATA_META / "backfill_observations"
COLS = ["date_start", "spend", "impressions", "inline_link_clicks",
        "purchases", "purchase_value", "checkouts_initiated"]
DELTA_METRICS = ["purchases", "purchase_value", "spend"]


def _load_snapshot(path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date_start"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=14, help="trailing days to snapshot")
    parser.add_argument("--asof", type=dt.date.fromisoformat, default=dt.date.today())
    args = parser.parse_args()

    src = DATA_META / "account_daily.csv"
    if not src.exists():
        sys.exit(f"{src} missing — run: python -m engine.fetch_meta --only account_daily")
    df = pd.read_csv(src, parse_dates=["date_start"])
    last_days = sorted(df["date_start"].dt.date.unique())[-args.window:]
    snap = df[df["date_start"].dt.date.isin(last_days)][[c for c in COLS if c in df.columns]].copy()
    snap["snapshot_asof"] = args.asof.isoformat()

    OBS_DIR.mkdir(parents=True, exist_ok=True)
    out = OBS_DIR / f"account_daily_asof_{args.asof.isoformat()}.csv"
    prior = sorted(p for p in OBS_DIR.glob("account_daily_asof_*.csv")
                   if p.name < out.name)
    snap.to_csv(out, index=False)
    print(f"[snapshot_backfill] {len(snap)} days ({last_days[0]} .. {last_days[-1]}) -> {out.relative_to(DATA_META)}")

    if not prior:
        print("[snapshot_backfill] no prior snapshot — this run is the reference; deltas start next run")
        return
    prev = _load_snapshot(prior[-1])
    prev_asof = prev["snapshot_asof"].iloc[0]
    merged = snap.merge(prev, on="date_start", suffixes=("_curr", "_prev"))
    if merged.empty:
        print(f"[snapshot_backfill] no overlapping days with {prior[-1].name}")
        return
    rows = pd.DataFrame({
        "date_start": merged["date_start"].dt.date,
        "prev_asof": prev_asof,
        "curr_asof": args.asof.isoformat(),
        "age_days": [(args.asof - d).days for d in merged["date_start"].dt.date],
    })
    for m in DELTA_METRICS:
        rows[f"{m}_prev"] = merged[f"{m}_prev"]
        rows[f"{m}_curr"] = merged[f"{m}_curr"]
        rows[f"{m}_delta"] = merged[f"{m}_curr"] - merged[f"{m}_prev"]
    deltas_path = OBS_DIR / "deltas.csv"
    rows.to_csv(deltas_path, mode="a", header=not deltas_path.exists(), index=False)
    moved = rows[(rows[[f"{m}_delta" for m in DELTA_METRICS]].fillna(0) != 0).any(axis=1)]
    print(f"[snapshot_backfill] vs {prev_asof}: {len(rows)} overlapping days, "
          f"{len(moved)} restated -> appended to {deltas_path.relative_to(DATA_META)}")
    if not moved.empty:
        with pd.option_context("display.width", 200):
            print(moved.to_string(index=False))


if __name__ == "__main__":
    main()
