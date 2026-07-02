"""Phase 1 — full-history anomaly timeline (detection only, no classification).

Runs the self-baseline model over the committed account_daily history, flags
anomaly windows (>= 2 consecutive days beyond +-2 sigma of the day-of-week
adjusted trailing-90d baseline), decomposes CPA windows into CPM / CTR / CVR
contributions, and writes reports/anomaly_timeline.md.

Usage: python -m engine.timeline
"""

from __future__ import annotations

import datetime as dt

from engine import baseline as bl
from engine.config import REPO_ROOT
from engine.decompose import decompose_window

REPORT = REPO_ROOT / "reports" / "anomaly_timeline.md"


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x:+.1%}"


def main() -> None:
    metrics = bl.load_metrics()
    baselines = bl.rolling_baselines(metrics)
    windows = bl.anomaly_windows(baselines)
    month_pos = bl.month_position_diagnostics(metrics)

    dates = metrics["date"]
    scored = baselines.dropna(subset=["z"])
    first_scored = scored["date"].min()
    cpa_windows = [w for w in windows if w["metric"] == "cpa"]
    other_windows = [w for w in windows if w["metric"] != "cpa"]

    lines: list[str] = []
    add = lines.append
    add("# Anomaly Timeline — full account history (Phase 1: detection only)")
    add("")
    add(f"Data: `data/meta/account_daily.csv`, {dates.min()} .. {dates.max()} "
        f"({len(metrics)} delivering days used).")
    add(f"Model: trailing-{bl.WINDOW_DAYS}d rolling baseline per metric, day-of-week adjusted, "
        f"log-space robust (median/MAD); anomaly = |z| >= {bl.Z_THRESHOLD:g} for >= {bl.MIN_RUN} "
        f"consecutive days. No labeling or classification in this phase.")
    add("")
    add("## Data-quality notes")
    add("")
    add(f"- **Delivery pause excluded from all baselines: {bl.PAUSE_START} .. {bl.PAUSE_END}** "
        "(account-level event `acct-delivery-pause-2026-02-27` in `signals/library.json`). "
        "Wider than the known 8-day data gap: Feb 27 - Mar 4 returned rows with zero "
        "spend/impressions, Mar 5 - 12 returned no rows. 2026-03-02 records 2 purchases "
        "against $0 spend — lagged attribution landing inside the pause.")
    add(f"- Warmup: baselines require >= {bl.MIN_WINDOW} trailing days, so scoring starts "
        f"{first_scored}; {dates.min()} .. {first_scored - dt.timedelta(days=1)} is unscored.")
    add("- `checkouts_initiated` first appears 2026-01-25 and is missing Jan 29 - Feb 2, 2026 "
        "on days that otherwise delivered normally — likely a checkout-event tracking gap, "
        "worth remembering when the verdict engine reasons about checkout_rate (flagged here "
        "as data quality, not classified).")
    add("- **checkout_rate steps x~6.5 overnight on 2026-05-24** (47 -> 287 checkouts "
        "day-over-day on similar clicks) and persists — a structural level shift consistent "
        "with an event-definition/tracking change, not gradual demand movement (account-level "
        "event `acct-checkout-event-shift-2026-05-24` in `signals/library.json`, not classified "
        "here). The long checkout_rate 'high' window starting 2026-05-24 is this shift being "
        "absorbed by the trailing baseline; checkout_rate comparisons spanning the date are "
        "invalid without segmenting.")
    add("- Post-pause days (2026-03-13 onward) are scored normally but carry learning-phase "
        "risk; the first flags after the pause should be read with that in mind.")
    add("")
    add("## Month-position diagnostics (NOT applied to z-scores)")
    add("")
    add(f"~7.5 months of history gives each bucket only a handful of same-position weeks and "
        "confounds bucket effects with trend/season, so these factors are reported for "
        "orientation only and are deliberately not folded into the baselines. Revisit at 12+ "
        "months.")
    add("")
    add("| metric | bucket | n days | factor vs overall median | approx SE |")
    add("|---|---|---|---|---|")
    for r in month_pos.itertuples():
        add(f"| {r.metric} | {r.bucket} | {r.n_days} | {r.factor_vs_overall:.3f} | "
            f"±{r.approx_se_of_factor:.3f} |")
    add("")
    add(f"## CPA anomaly windows ({len(cpa_windows)})")
    add("")
    if not cpa_windows:
        add("None detected.")
    for w in cpa_windows:
        d = decompose_window(baselines, w["start"], w["end"])
        arrow = "▲" if w["direction"] == "high" else "▼"
        add(f"### {w['start']} .. {w['end']} — CPA {arrow} {_pct(w['mean_pct_vs_baseline'])} "
            f"vs baseline ({w['days']} days, mean z {w['mean_z']:+.1f}, peak z {w['peak_z']:+.1f})")
        add("")
        add("| component | vs own baseline | share of CPA drift | days used |")
        add("|---|---|---|---|")
        for m in ("cpm", "ctr", "cvr"):
            c = d["components"][m]
            share = c["share_of_cpa_drift"]
            share_s = "n/a" if share != share else f"{share:.0%}"
            add(f"| {m.upper()} | {_pct(c['pct_vs_baseline'])} | {share_s} | {c['days_used']} |")
        add(f"| _identity residual_ | dlog {d['identity_residual_dlog']:+.3f} | — | — |")
        add("")
    add(f"## Other metric anomaly windows ({len(other_windows)})")
    add("")
    add("| metric | window | days | direction | vs baseline | mean z | peak z |")
    add("|---|---|---|---|---|---|---|")
    for w in other_windows:
        add(f"| {w['metric']} | {w['start']} .. {w['end']} | {w['days']} | {w['direction']} | "
            f"{_pct(w['mean_pct_vs_baseline'])} | {w['mean_z']:+.1f} | {w['peak_z']:+.1f} |")
    add("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    print(f"[timeline] {len(cpa_windows)} CPA windows, {len(other_windows)} other-metric windows "
          f"-> {REPORT.relative_to(REPO_ROOT)}")
    for w in windows:
        print(f"  {w['metric']:>14s} {w['start']} .. {w['end']} ({w['days']}d) "
              f"{w['direction']:>4s} {_pct(w['mean_pct_vs_baseline'])} peak z {w['peak_z']:+.1f}")


if __name__ == "__main__":
    main()
