"""Phase 1 — self-baseline model (brief §5).

Trailing-90-day rolling baselines per metric, day-of-week adjusted, computed
in log space from the account's own history only (no peer network).

Metrics are derived from raw account_daily columns so the CPA identity holds
exactly:

    cpm  = spend / impressions * 1000
    ctr  = inline_link_clicks / impressions      (link CTR, not Meta's all-click ctr)
    cvr  = purchases / inline_link_clicks
    cpa  = spend / purchases
    checkout_rate = checkouts_initiated / inline_link_clicks
    spend

    =>  cpa == cpm / (1000 * ctr * cvr)
    =>  log cpa == log cpm - log ctr - log cvr - log 1000   (decomposition is
        exactly additive in log space; see engine/decompose.py)

Method, per (metric, day t):
    window   = valid days in [t-90d, t-1d], excluding EXCLUDE_DATES
    warmup   = no baseline until the window holds >= MIN_WINDOW days
    dow(t)   = median(log m | weekday) - median(log m), applied only when that
               weekday has >= MIN_DOW_OBS observations in the window
    expected = exp(median(log m) + dow_offset)
    sigma    = 1.4826 * MAD of dow-adjusted log residuals over the window,
               floored at SIGMA_FLOOR
    z(t)     = (log m(t) - log expected(t)) / sigma

Exclusions: the 2026-02-27 .. 2026-03-12 delivery pause. Note this is WIDER
than the known 8-day data gap: Feb 27 - Mar 4 returned rows with zero
spend/impressions, Mar 5 - 12 returned no rows at all. Registered as an
account-level event in signals/library.json. Zero-delivery days produce no
metrics and would poison trailing medians and MADs.

Month-position buckets (early 1-10 / mid 11-20 / late 21-31) are computed as
FULL-HISTORY diagnostics with explicit uncertainty and are NOT folded into
z-scores: with ~7.5 months of history each bucket holds ~7 same-position
weeks and bucket effects confound with trend and season. Revisit at 12+
months of history.

Anomaly: |z| >= Z_THRESHOLD for >= MIN_RUN consecutive calendar days.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from engine.config import DATA_META

METRICS = ["cpa", "cpm", "ctr", "cvr", "spend", "checkout_rate"]

WINDOW_DAYS = 90
MIN_WINDOW = 28       # warmup: no baseline until this many valid trailing days
MIN_DOW_OBS = 3       # weekday offset needs at least this many observations
SIGMA_FLOOR = 0.01    # log-space; ~1% — guards degenerate MADs on flat metrics
Z_THRESHOLD = 2.0
MIN_RUN = 2

# Delivery pause: zero delivery Feb 27 - Mar 4 (rows present, spend = 0),
# no rows Mar 5 - 12. See signals/library.json: acct-delivery-pause-2026-02-27.
PAUSE_START = dt.date(2026, 2, 27)
PAUSE_END = dt.date(2026, 3, 12)
EXCLUDE_DATES = {PAUSE_START + dt.timedelta(days=i)
                 for i in range((PAUSE_END - PAUSE_START).days + 1)}

MONTH_BUCKETS = [("early(1-10)", 1, 10), ("mid(11-20)", 11, 20), ("late(21-31)", 21, 31)]


def load_metrics(path=None) -> pd.DataFrame:
    """account_daily -> per-day derived metrics, delivery pause excluded."""
    df = pd.read_csv(path or DATA_META / "account_daily.csv", parse_dates=["date_start"])
    df["date"] = df["date_start"].dt.date
    df = df[~df["date"].isin(EXCLUDE_DATES)].copy()
    zero_delivery = df["impressions"] <= 0
    if zero_delivery.any():  # zero-delivery days outside the known pause
        raise ValueError(
            f"unexpected zero-delivery days outside the registered pause: "
            f"{sorted(df.loc[zero_delivery, 'date'])} — extend EXCLUDE_DATES "
            f"and signals/library.json"
        )
    out = pd.DataFrame({"date": df["date"]})
    out["spend"] = df["spend"]
    out["cpm"] = df["spend"] / df["impressions"] * 1000
    out["ctr"] = df["inline_link_clicks"] / df["impressions"]
    out["cvr"] = df["purchases"] / df["inline_link_clicks"].where(df["inline_link_clicks"] > 0)
    out["cpa"] = df["spend"] / df["purchases"].where(df["purchases"] > 0)
    out["checkout_rate"] = (
        df["checkouts_initiated"] / df["inline_link_clicks"].where(df["inline_link_clicks"] > 0)
    )
    return out.sort_values("date").reset_index(drop=True)


def _baseline_one_day(logs: pd.Series, dows: pd.Series, target_dow: int) -> tuple[float, float]:
    """(expected_log, sigma) for a target weekday given a trailing window."""
    center = logs.median()
    offsets = {}
    for dow, grp in logs.groupby(dows):
        if len(grp) >= MIN_DOW_OBS:
            offsets[dow] = grp.median() - center
    resid = logs - (center + dows.map(offsets).fillna(0.0))
    sigma = max(1.4826 * resid.abs().median(), SIGMA_FLOOR)
    return center + offsets.get(target_dow, 0.0), sigma


def rolling_baselines(metrics: pd.DataFrame) -> pd.DataFrame:
    """Tidy frame: date, metric, value, expected, z, sigma, n_window."""
    rows = []
    dates = metrics["date"]
    for name in METRICS:
        valid = metrics[["date", name]].dropna()
        valid = valid[valid[name] > 0]
        logs_by_date = pd.Series(
            np.log(valid[name].to_numpy()), index=pd.Index(valid["date"]))
        for t in dates:
            value = metrics.loc[metrics["date"] == t, name].iloc[0]
            lo = t - dt.timedelta(days=WINDOW_DAYS)
            win = logs_by_date[(logs_by_date.index >= lo) & (logs_by_date.index < t)]
            if len(win) < MIN_WINDOW or pd.isna(value) or value <= 0:
                rows.append((t, name, value, np.nan, np.nan, np.nan, len(win)))
                continue
            dows = pd.Series([d.weekday() for d in win.index], index=win.index)
            expected_log, sigma = _baseline_one_day(win, dows, t.weekday())
            z = (np.log(value) - expected_log) / sigma
            rows.append((t, name, value, np.exp(expected_log), z, sigma, len(win)))
    return pd.DataFrame(rows, columns=["date", "metric", "value", "expected", "z", "sigma", "n_window"])


def month_position_diagnostics(metrics: pd.DataFrame) -> pd.DataFrame:
    """Full-history month-position factors — diagnostic only, wide uncertainty."""
    rows = []
    for name in METRICS:
        valid = metrics[["date", name]].dropna()
        valid = valid[valid[name] > 0]
        logs = np.log(valid[name])
        center = logs.median()
        for label, lo, hi in MONTH_BUCKETS:
            mask = valid["date"].map(lambda d: lo <= d.day <= hi)
            grp = logs[mask]
            if len(grp) < 5:
                continue
            spread = 1.4826 * (grp - grp.median()).abs().median()
            rows.append({
                "metric": name, "bucket": label, "n_days": len(grp),
                "factor_vs_overall": float(np.exp(grp.median() - center)),
                "approx_se_of_factor": float(spread / np.sqrt(len(grp))),
            })
    return pd.DataFrame(rows)


def anomaly_windows(baselines: pd.DataFrame) -> list[dict]:
    """Runs of >= MIN_RUN consecutive calendar days with |z| >= Z_THRESHOLD."""
    windows = []
    for name, grp in baselines.groupby("metric"):
        grp = grp.dropna(subset=["z"]).sort_values("date")
        run: list[pd.Series] = []
        def flush():
            if len(run) >= MIN_RUN:
                zs = [r.z for r in run]
                ratios = [r.value / r.expected for r in run]
                windows.append({
                    "metric": name,
                    "start": run[0].date, "end": run[-1].date, "days": len(run),
                    "direction": "high" if zs[0] > 0 else "low",
                    "mean_z": float(np.mean(zs)),
                    "peak_z": float(max(zs, key=abs)),
                    "mean_pct_vs_baseline": float(np.exp(np.mean(np.log(ratios))) - 1),
                })
        for row in grp.itertuples():
            flagged = abs(row.z) >= Z_THRESHOLD
            same_sign = not run or (row.z > 0) == (run[-1].z > 0)
            consecutive = not run or (row.date - run[-1].date).days == 1
            if flagged and same_sign and consecutive:
                run.append(row)
            else:
                flush()
                run = [row] if flagged else []
        flush()
    return sorted(windows, key=lambda w: (w["start"], w["metric"]))
