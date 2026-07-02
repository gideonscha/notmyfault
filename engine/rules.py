"""Phase 2 — recurring-rules engine.

Expands the recurring rules in signals/library.json into per-date flags over
an arbitrary window, and computes account-specific response coefficients from
the account's own baseline residuals (anti-horoscope rule: no external signal
enters a verdict without a quantified, dated, account-specific effect
estimate — or an explicit "correlation only, coefficient unknown" flag).

Coefficient method, per rule x metric:
    flagged days -> dlog = log(value / expected) against the day-of-week-
    adjusted trailing-90d baseline (engine/baseline.py), so weekday effects
    are already removed. coefficient = median dlog, spread = 1.4826 * MAD.
    Rules with fewer than MIN_OCCURRENCES occurrences in the window keep
    coefficient: null (prior only). An "occurrence" is one calendar hit of
    the rule (one payday, one holiday, one issuance window), not one day.

`python -m engine.rules` recomputes coefficients and writes them back into
signals/library.json under rules.<id>.coefficients.
"""

from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from engine import baseline as bl
from engine.config import REPO_ROOT

LIBRARY = REPO_ROOT / "signals" / "library.json"
MIN_OCCURRENCES = 4
COEF_METRICS = ["cpa", "cpm", "ctr", "cvr", "spend"]


def load_library() -> dict:
    return json.loads(LIBRARY.read_text())


def _dst_transitions(year: int) -> list[dt.date]:
    """US statutory transitions: 2nd Sunday of March, 1st Sunday of November."""
    out = []
    for month, nth in ((3, 2), (11, 1)):
        d = dt.date(year, month, 1)
        d += dt.timedelta(days=(6 - d.weekday()) % 7)  # first Sunday
        out.append(d + dt.timedelta(days=7 * (nth - 1)))
    return out


def expand_rule(rule_id: str, rule: dict, start: dt.date, end: dt.date,
                signals: list[dict] | None = None) -> list[tuple[dt.date, int]]:
    """(date, occurrence_index) pairs for one rule within [start, end]."""
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    kind = rule["kind"]
    if kind == "day_of_month":
        hits = [d for d in days if d.day == rule["day"]]
        return [(d, i) for i, d in enumerate(hits)]
    if kind == "last_day_of_month":
        hits = [d for d in days if (d + dt.timedelta(days=1)).day == 1]
        return [(d, i) for i, d in enumerate(hits)]
    if kind == "day_of_month_range":
        out, occ = [], -1
        for d in days:
            if rule["day_start"] <= d.day <= rule["day_end"]:
                if d.day == rule["day_start"] or not out or out[-1][0] != d - dt.timedelta(days=1):
                    occ += 1
                out.append((d, occ))
        return out
    if kind == "date_list":
        hits = [dt.date.fromisoformat(s) for s in rule["dates"]]
        return [(d, i) for i, d in enumerate(h for h in hits if start <= h <= end)]
    if kind == "date_range":
        lo = max(start, dt.date.fromisoformat(rule["date_start"]))
        hi = min(end, dt.date.fromisoformat(rule["date_end"]))
        return [(lo + dt.timedelta(days=i), 0) for i in range((hi - lo).days + 1)] if lo <= hi else []
    if kind == "dst_transitions":
        hits = [d for y in range(start.year, end.year + 1)
                for d in _dst_transitions(y) if start <= d <= end]
        return [(d, i) for i, d in enumerate(sorted(hits))]
    if kind == "from_signals":
        hits = sorted(dt.date.fromisoformat(s["date_start"]) for s in (signals or [])
                      if s["id"].startswith(rule["signal_prefix"])
                      and start <= dt.date.fromisoformat(s["date_start"]) <= end)
        return [(d, i) for i, d in enumerate(hits)]
    raise ValueError(f"unknown rule kind {kind!r} for {rule_id!r}")


def expand_all(start: dt.date, end: dt.date, library: dict | None = None) -> pd.DataFrame:
    """Tidy frame: date, rule_id, occurrence."""
    lib = library or load_library()
    rows = [(d, rid, occ)
            for rid, rule in lib["rules"].items() if not rid.startswith("_")
            for d, occ in expand_rule(rid, rule, start, end, lib["signals"])]
    return pd.DataFrame(rows, columns=["date", "rule_id", "occurrence"])


def compute_coefficients(baselines: pd.DataFrame, flags: pd.DataFrame) -> dict:
    """Per-rule, per-metric median dlog on flagged days (see module doc)."""
    scored = baselines.dropna(subset=["z"]).copy()
    scored["dlog"] = np.log(scored["value"] / scored["expected"])
    out: dict[str, dict] = {}
    for rule_id, grp in flags.groupby("rule_id"):
        dates = set(grp["date"])
        n_occ = grp["occurrence"].nunique()
        entry: dict = {"n_occurrences_in_window": int(n_occ),
                       "method": "median day-of-week-adjusted log residual on flagged days",
                       "computed_at": None, "metrics": None}
        if n_occ < MIN_OCCURRENCES:
            entry["status"] = f"prior only — {n_occ} occurrence(s) < {MIN_OCCURRENCES}, coefficient unknown"
        else:
            metrics = {}
            for m in COEF_METRICS:
                g = scored[(scored["metric"] == m) & (scored["date"].isin(dates))]
                if len(g) < MIN_OCCURRENCES:
                    metrics[m] = None
                    continue
                med = float(g["dlog"].median())
                mad = float(1.4826 * (g["dlog"] - g["dlog"].median()).abs().median())
                metrics[m] = {"dlog_median": round(med, 4),
                              "pct_effect": round(float(np.exp(med) - 1), 4),
                              "mad": round(mad, 4), "n_days": int(len(g))}
            entry["metrics"] = metrics
            entry["status"] = "computed"
        out[rule_id] = entry
    return out


def main() -> None:
    lib = load_library()
    metrics = bl.load_metrics()
    baselines = bl.rolling_baselines(metrics)
    start, end = metrics["date"].min(), metrics["date"].max()
    flags = expand_all(start, end, lib)
    coefs = compute_coefficients(baselines, flags)
    stamp = end.isoformat()  # stamped with data-window end, not wall clock
    for rule_id, entry in coefs.items():
        entry["computed_at"] = f"data through {stamp}"
        lib["rules"][rule_id]["coefficients"] = entry
    LIBRARY.write_text(json.dumps(lib, indent=2) + "\n")
    print(f"[rules] window {start} .. {end}: {len(flags)} flag-days across "
          f"{flags['rule_id'].nunique()} rules -> coefficients written to {LIBRARY.relative_to(REPO_ROOT)}")
    for rule_id, entry in sorted(coefs.items()):
        line = f"  {rule_id:>18s} occ={entry['n_occurrences_in_window']:>2d} {entry['status']}"
        if entry["metrics"]:
            cvr = entry["metrics"].get("cvr")
            cpa = entry["metrics"].get("cpa")
            if cvr:
                line += f" | cvr {cvr['pct_effect']:+.1%} (n={cvr['n_days']})"
            if cpa:
                line += f" | cpa {cpa['pct_effect']:+.1%} (n={cpa['n_days']})"
        print(line)


if __name__ == "__main__":
    main()
