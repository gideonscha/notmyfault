"""Phase 2 — signal coverage report (no verdicts).

Joins every Phase 1 anomaly window against the signal library: dated events
that overlap (or sit within ADJACENT_DAYS of) the window, and recurring-rule
flags inside the window with their account-specific coefficients where
computed. Classification is Phase 3; this report only shows what evidence
exists near each anomaly.

Usage: python -m engine.coverage  ->  reports/signal_coverage.md
"""

from __future__ import annotations

import datetime as dt
import json

from engine import baseline as bl
from engine import rules as rl
from engine.config import REPO_ROOT

REPORT = REPO_ROOT / "reports" / "signal_coverage.md"
ADJACENT_DAYS = 2


def _event_spans(sig: dict, data_end: dt.date) -> list[tuple[dt.date, dt.date]]:
    """One (start, end) span per event — or one per date for multi-date events."""
    if "dates" in sig:
        return [(d, d) for d in map(dt.date.fromisoformat, sig["dates"])]
    start = dt.date.fromisoformat(sig["date_start"])
    end = dt.date.fromisoformat(sig["date_end"]) if sig.get("date_end") else data_end
    return [(start, end)]


def main() -> None:
    lib = rl.load_library()
    metrics = bl.load_metrics()
    baselines = bl.rolling_baselines(metrics)
    windows = bl.anomaly_windows(baselines)
    data_end = metrics["date"].max()
    flags = rl.expand_all(metrics["date"].min(), data_end, lib)

    lines: list[str] = []
    add = lines.append
    add("# Signal Coverage — Phase 1 anomaly windows x signal library (no verdicts)")
    add("")
    add(f"{len(windows)} anomaly windows (engine/baseline.py, |z| >= {bl.Z_THRESHOLD:g} x "
        f">= {bl.MIN_RUN}d) joined against {len(lib['signals'])} dated signals and "
        f"{sum(1 for k in lib['rules'] if not k.startswith('_'))} recurring rules. "
        f"Events marked *adjacent* start within ±{ADJACENT_DAYS} days of the window. "
        "Rule coefficients are account-specific median log-residual effects "
        "(engine/rules.py); 'prior only' = fewer than 4 occurrences, coefficient unknown "
        "(anti-horoscope rule). Classification is deliberately absent — Phase 3.")
    add("")
    add("NOTE: signals/library.json carries `_pending`: the library_seed.json attachment "
        "did not reach the container; this report regenerates in seconds once the seed "
        "is merged (`python -m engine.coverage`).")
    add("")
    add("| # | window | metric | dir | vs baseline | overlapping events | adjacent events | rule flags (coef for window metric) |")
    add("|---|---|---|---|---|---|---|---|")

    uncovered = []
    for i, w in enumerate(windows, 1):
        overlap, adjacent = [], []
        for sig in lib["signals"]:
            spans = _event_spans(sig, data_end)
            tag = sig["id"] + ("" if sig["verified"] else " (UNVERIFIED)")
            if any(s <= w["end"] and e >= w["start"] for s, e in spans):
                overlap.append(tag)
            elif any(abs((s - w["end"]).days) <= ADJACENT_DAYS
                     or abs((w["start"] - e).days) <= ADJACENT_DAYS for s, e in spans):
                adjacent.append(tag)
        in_win = flags[(flags["date"] >= w["start"]) & (flags["date"] <= w["end"])]
        rule_bits = []
        for rid in sorted(in_win["rule_id"].unique()):
            coefs = (lib["rules"][rid].get("coefficients") or {})
            m = (coefs.get("metrics") or {}).get(w["metric"])
            if m:
                rule_bits.append(f"{rid} ({m['pct_effect']:+.1%})")
            elif coefs.get("status") == "computed":
                rule_bits.append(f"{rid} (no coef for {w['metric']})")
            else:
                rule_bits.append(f"{rid} (prior only)")
        if not overlap and not adjacent:
            uncovered.append((i, w))
        add(f"| {i} | {w['start']} .. {w['end']} | {w['metric']} | {w['direction']} | "
            f"{w['mean_pct_vs_baseline']:+.1%} | {'; '.join(overlap) or '—'} | "
            f"{'; '.join(adjacent) or '—'} | {'; '.join(rule_bits) or '—'} |")

    add("")
    add(f"## Windows with no dated-event coverage ({len(uncovered)})")
    add("")
    add("Anomalies explained (if at all) only by recurring rules or by nothing in the "
        "library yet — the priority list for library expansion (and the honest "
        "'unexplained' pool Phase 3 must be willing to leave unexplained):")
    add("")
    for i, w in uncovered:
        add(f"- #{i} {w['metric']} {w['direction']} {w['start']} .. {w['end']} "
            f"({w['mean_pct_vs_baseline']:+.1%})")
    add("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    print(f"[coverage] {len(windows)} windows, {len(uncovered)} without dated-event coverage "
          f"-> {REPORT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
