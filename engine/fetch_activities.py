"""Phase 3 — ad account activity log pull (account-changes evidence stream).

GET /act_{id}/activities: budget moves, status flips, bid/targeting edits,
creative changes — the advertiser's own actions, i.e. the INTERNAL_ADS
evidence stream. Lands data/meta/activity_log.csv + .parquet.

Read-only. Runs on GitHub Actions (cloud containers cannot reach
graph.facebook.com — see CLAUDE.md data-layer boundaries).

RETENTION CAVEAT: Meta does not document a hard retention floor for this
endpoint; if the earliest returned event is materially later than --since,
the pull prints a truncation warning — treat missing early history as
"unknown", not "no changes".

Usage: python -m engine.fetch_activities --since 2025-11-01
"""

from __future__ import annotations

import argparse
import datetime as dt

import pandas as pd
import requests

from engine.config import DATA_META, load_config
from engine.fetch_meta import GRAPH, _get

FIELDS = [
    "event_time",
    "event_type",
    "translated_event_type",
    "actor_id",
    "actor_name",
    "application_name",
    "object_id",
    "object_name",
    "object_type",
    "extra_data",
]


def run_pull(since: dt.date, until: dt.date) -> pd.DataFrame:
    cfg = load_config()
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {cfg.access_token}"
    url = f"{GRAPH}/{cfg.api_version}/{cfg.ad_account_id}/activities"
    params = {
        "fields": ",".join(FIELDS),
        "limit": 500,
        "since": since.isoformat(),
        "until": until.isoformat(),
    }
    rows: list[dict] = []
    payload = _get(session, url, params)
    while True:
        rows.extend(payload.get("data", []))
        next_url = payload.get("paging", {}).get("next")
        if not next_url:
            break
        payload = _get(session, next_url, None)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["extra_data"] = df.get("extra_data", pd.Series(dtype=str)).astype(str)
        df["event_time"] = pd.to_datetime(df["event_time"])
        df = df.sort_values("event_time").reset_index(drop=True)
    DATA_META.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_META / "activity_log.csv", index=False)
    df.to_parquet(DATA_META / "activity_log.parquet", index=False)
    if df.empty:
        print("[activities] 0 events returned — treat as UNKNOWN, not 'no changes'")
    else:
        earliest = df["event_time"].min().date()
        print(f"[activities] {len(df)} events, {earliest} .. {df['event_time'].max().date()} "
              f"-> activity_log.csv, activity_log.parquet")
        if earliest > since + dt.timedelta(days=3):
            print(f"[activities] WARNING: earliest event {earliest} is later than --since {since} "
                  f"— possible endpoint retention truncation; earlier history is UNKNOWN")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=dt.date.fromisoformat, default=dt.date(2025, 11, 1))
    parser.add_argument("--until", type=dt.date.fromisoformat, default=dt.date.today())
    args = parser.parse_args()
    run_pull(args.since, args.until)


if __name__ == "__main__":
    main()
