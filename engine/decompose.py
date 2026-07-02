"""Phase 1 — CPA decomposition (brief §4).

    CPA = CPM / (1000 * CTR * CVR)
    log CPA = log CPM - log CTR - log CVR - log 1000

Because the identity is exact in log space, a CPA drift vs baseline splits
additively into component drifts, each measured against that component's OWN
day-of-week-adjusted baseline:

    dlog(CPA_t) ~= dlog(CPM_t) - dlog(CTR_t) - dlog(CVR_t)      where
    dlog(m_t) = log(value_t / expected_t)

The residual term (baselines are independent medians, so the identity over
expectations is only approximate) is reported, never silently dropped.

Layer implication table (brief §4) — used by the Phase 3 verdict engine, NOT
by this module; Phase 1 is detection + decomposition only:

    | Pattern                     | Primary suspect                    |
    |-----------------------------|------------------------------------|
    | CPM up, CTR/CVR flat        | EXTERNAL_AUCTION                   |
    | CTR down, CPM flat          | creative fatigue OR delivery shift |
    | CVR down, upstream flat     | INTERNAL_FUNNEL OR EXTERNAL_DEMAND |
    | all bad, recovers on repull | REPORTING_ARTIFACT (check FIRST)   |
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

COMPONENTS = {"cpm": +1.0, "ctr": -1.0, "cvr": -1.0}  # sign in the log identity


def decompose_window(baselines: pd.DataFrame, start: dt.date, end: dt.date) -> dict:
    """Split a window's mean CPA drift (vs baseline) into component contributions.

    Returns per-metric mean % vs baseline, each component's contribution to
    the CPA log-drift, its share of that drift, and the identity residual.
    Days lacking a baseline or a defined metric are skipped per-metric; the
    day counts used are reported.
    """
    win = baselines[(baselines["date"] >= start) & (baselines["date"] <= end)]

    def mean_dlog(metric: str) -> tuple[float, int]:
        g = win[(win["metric"] == metric)].dropna(subset=["z"])
        if g.empty:
            return np.nan, 0
        dlogs = np.log(g["value"] / g["expected"])
        return float(dlogs.mean()), len(g)

    cpa_dlog, cpa_n = mean_dlog("cpa")
    out = {
        "start": start, "end": end,
        "cpa_pct_vs_baseline": float(np.exp(cpa_dlog) - 1) if not np.isnan(cpa_dlog) else np.nan,
        "cpa_days_used": cpa_n,
        "components": {},
    }
    contrib_sum = 0.0
    for metric, sign in COMPONENTS.items():
        dlog, n = mean_dlog(metric)
        contribution = sign * dlog if not np.isnan(dlog) else 0.0
        contrib_sum += contribution
        out["components"][metric] = {
            "pct_vs_baseline": float(np.exp(dlog) - 1) if not np.isnan(dlog) else np.nan,
            "contribution_dlog": float(contribution),
            "share_of_cpa_drift": (
                float(contribution / cpa_dlog)
                if cpa_dlog and not np.isnan(cpa_dlog) else np.nan
            ),
            "days_used": n,
        }
    out["identity_residual_dlog"] = (
        float(cpa_dlog - contrib_sum) if not np.isnan(cpa_dlog) else np.nan
    )
    return out
