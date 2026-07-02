"""Phase 0 data pull — Meta Marketing API daily insights to data/meta/.

Pulls, for the configured ad account over a date range (default: trailing 12
months through yesterday):

  1. account_daily          — account-level daily insights
  2. campaign_daily         — campaign-level daily insights
  3. account_daily_placement — account-level daily, broken down by
                               publisher_platform x platform_position
  4. account_daily_demo     — account-level daily, broken down by age x gender

Each pull is written as both CSV and parquet under data/meta/. Deterministic
re-runs: same range in, same files out (modulo Meta-side attribution restatement
of the trailing ~72h — which is itself a signal the engine uses).

Usage:
    python -m engine.fetch_meta                    # trailing 365 days
    python -m engine.fetch_meta --since 2025-07-01 --until 2026-07-01
    python -m engine.fetch_meta --only account_daily

Read-only: uses GET /insights exclusively. Never modifies the account.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from typing import Iterator

import pandas as pd
import requests

from engine.config import DATA_META, load_config

GRAPH = "https://graph.facebook.com"

# Sync insights calls over long ranges time out; chunk the range and let
# time_increment=1 return one row per day within each chunk.
CHUNK_DAYS = 30
PAGE_LIMIT = 500
MAX_RETRIES = 5

BASE_FIELDS = [
    "date_start",
    "date_stop",
    "spend",
    "impressions",
    "reach",
    "frequency",
    "cpm",
    "clicks",
    "cpc",
    "ctr",
    "inline_link_clicks",
    "inline_link_click_ctr",
    "actions",
    "action_values",
    "purchase_roas",
]

CAMPAIGN_FIELDS = ["campaign_id", "campaign_name"] + BASE_FIELDS

# Action types that constitute a purchase, in preference order (omni first).
PURCHASE_ACTION_TYPES = [
    "omni_purchase",
    "offsite_conversion.fb_pixel_purchase",
    "purchase",
]
CHECKOUT_ACTION_TYPES = [
    "omni_initiated_checkout",
    "offsite_conversion.fb_pixel_initiate_checkout",
    "initiate_checkout",
]

PULLS: dict[str, dict] = {
    "account_daily": {"level": "account", "fields": BASE_FIELDS, "breakdowns": None},
    "campaign_daily": {"level": "campaign", "fields": CAMPAIGN_FIELDS, "breakdowns": None},
    "account_daily_placement": {
        "level": "account",
        "fields": BASE_FIELDS,
        "breakdowns": "publisher_platform,platform_position",
    },
    "account_daily_demo": {
        "level": "account",
        "fields": BASE_FIELDS,
        "breakdowns": "age,gender",
    },
}


def _chunks(since: dt.date, until: dt.date) -> Iterator[tuple[dt.date, dt.date]]:
    cur = since
    while cur <= until:
        end = min(cur + dt.timedelta(days=CHUNK_DAYS - 1), until)
        yield cur, end
        cur = end + dt.timedelta(days=1)


def _get(session: requests.Session, url: str, params: dict | None) -> dict:
    """GET with retry/backoff on rate limits and transient errors."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, params=params, timeout=120)
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  network error ({exc.__class__.__name__}), retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        if resp.status_code == 200:
            return resp.json()
        try:
            err = resp.json().get("error", {})
        except ValueError:
            err = {}
        code = err.get("code")
        transient = resp.status_code >= 500 or code in (1, 2, 4, 17, 32, 613, 80000, 80004)
        if transient and attempt < MAX_RETRIES - 1:
            wait = 2 ** (attempt + 2)  # rate limits want longer waits: 4,8,16,32s
            print(
                f"  API error code={code} status={resp.status_code} "
                f"({err.get('message', '')[:120]}), retry in {wait}s",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue
        raise RuntimeError(
            f"Meta API error status={resp.status_code} code={code}: "
            f"{err.get('message', resp.text[:300])}"
        )
    raise RuntimeError("unreachable")


def _fetch_window(
    session: requests.Session,
    cfg,
    pull: dict,
    since: dt.date,
    until: dt.date,
) -> list[dict]:
    url = f"{GRAPH}/{cfg.api_version}/{cfg.ad_account_id}/insights"
    params: dict = {
        "access_token": cfg.access_token,
        "level": pull["level"],
        "fields": ",".join(pull["fields"]),
        "time_increment": 1,
        "time_range": json.dumps({"since": since.isoformat(), "until": until.isoformat()}),
        "limit": PAGE_LIMIT,
    }
    if pull["breakdowns"]:
        params["breakdowns"] = pull["breakdowns"]
    rows: list[dict] = []
    payload = _get(session, url, params)
    while True:
        rows.extend(payload.get("data", []))
        next_url = payload.get("paging", {}).get("next")
        if not next_url:
            return rows
        payload = _get(session, next_url, None)  # next URL embeds all params


def _sum_actions(row: dict, key: str, action_types: list[str]) -> float | None:
    """Extract the first matching action type's value from an actions list."""
    entries = {e.get("action_type"): e.get("value") for e in row.get(key) or []}
    for action_type in action_types:
        if action_type in entries:
            try:
                return float(entries[action_type])
            except (TypeError, ValueError):
                return None
    return None


def _flatten(rows: list[dict], breakdowns: str | None) -> pd.DataFrame:
    out = []
    breakdown_cols = breakdowns.split(",") if breakdowns else []
    for row in rows:
        rec = {k: v for k, v in row.items() if k not in ("actions", "action_values", "purchase_roas")}
        rec["purchases"] = _sum_actions(row, "actions", PURCHASE_ACTION_TYPES)
        rec["purchase_value"] = _sum_actions(row, "action_values", PURCHASE_ACTION_TYPES)
        rec["checkouts_initiated"] = _sum_actions(row, "actions", CHECKOUT_ACTION_TYPES)
        roas = row.get("purchase_roas") or []
        rec["purchase_roas"] = float(roas[0]["value"]) if roas else None
        out.append(rec)
    df = pd.DataFrame(out)
    if df.empty:
        return df
    numeric = [
        c
        for c in df.columns
        if c
        not in ["date_start", "date_stop", "campaign_id", "campaign_name", *breakdown_cols]
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Derived: CPA (cost per purchase) and CVR (link click -> purchase)
    df["cpa"] = df["spend"] / df["purchases"].where(df["purchases"] > 0)
    df["cvr"] = df["purchases"] / df["inline_link_clicks"].where(df["inline_link_clicks"] > 0)
    sort_cols = ["date_start"] + [c for c in ("campaign_id", *breakdown_cols) if c in df.columns]
    return df.sort_values(sort_cols).reset_index(drop=True)


def run_pull(name: str, since: dt.date, until: dt.date) -> pd.DataFrame:
    cfg = load_config()
    pull = PULLS[name]
    session = requests.Session()
    all_rows: list[dict] = []
    for chunk_start, chunk_end in _chunks(since, until):
        print(f"[{name}] {chunk_start} .. {chunk_end}", flush=True)
        all_rows.extend(_fetch_window(session, cfg, pull, chunk_start, chunk_end))
    df = _flatten(all_rows, pull["breakdowns"])
    DATA_META.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_META / f"{name}.csv"
    pq_path = DATA_META / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)
    print(f"[{name}] {len(df)} rows -> {csv_path.name}, {pq_path.name}", flush=True)
    return df


def main() -> None:
    yesterday = dt.date.today() - dt.timedelta(days=1)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=dt.date.fromisoformat, default=yesterday - dt.timedelta(days=364))
    parser.add_argument("--until", type=dt.date.fromisoformat, default=yesterday)
    parser.add_argument("--only", choices=sorted(PULLS), help="run a single pull")
    args = parser.parse_args()

    names = [args.only] if args.only else list(PULLS)
    for name in names:
        run_pull(name, args.since, args.until)


if __name__ == "__main__":
    main()
