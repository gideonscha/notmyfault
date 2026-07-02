# NOTMYFAULT — Meta Performance Exculpation Engine

For a Meta advertiser with a sudden multi-day CPA/ROAS deterioration, answers one
question: **was it something you did, or something in the environment?** Output is a
verdict report — classified, evidence-backed, confidence-scored. See `CLAUDE.md` for
verdict classes and operating rules.

## Setup

```bash
pip install requests pandas pyarrow
cp .env.example .env   # then fill in META_ACCESS_TOKEN (see .env.example comments)
```

## Phase 0 — data pull

```bash
python -m engine.fetch_meta            # trailing 365 days, all four pulls
python -m engine.verify_pull           # row counts, date coverage, sample rows
```

Pulls land in `data/meta/` (committed to the repo — see `CLAUDE.md`) as CSV +
parquet: `account_daily`, `campaign_daily`, `account_daily_placement`,
`account_daily_demo`. In production the pull runs daily at 06:00 UTC via
`.github/workflows/daily-pull.yml` (GitHub Actions runners can reach
`graph.facebook.com`; Claude Code cloud containers cannot — egress policy).
Each run also writes a dated trailing-window snapshot to
`data/meta/backfill_observations/` (`engine/snapshot_backfill.py`); the
accumulated per-day deltas are the account's empirical attribution-lag curve.
`engine/verify_baseline.py` pins every re-pull to the frozen local Phase 0
aggregates (216 rows / $368,070.58 / 2025-11-20→2026-07-01 / gap 2026-03-05→12).

Workflow setup (one-time): add `META_ACCESS_TOKEN` and `META_AD_ACCOUNT_ID`
to the repo's Actions Secrets, and note the cron only fires from the default
branch.

## Layout

```
engine/     fetch_meta.py + verify_pull.py (Phase 0), baseline/decompose (Phase 1),
            correlate/verdict (Phase 3)
signals/    library.json — verified external events + calendar rules (Phase 2)
backtest/   incidents.json — labeled ground truth; run_backtest.py (Phase 4)
data/       pulled Meta history (gitignored)
reports/    generated verdict reports
```

## Status

- [x] Phase 0 — scaffold, .env handling, pull scripts
- [x] Phase 0 — full-history data pull (runs on GitHub Actions; first pull committed
  2026-07-02, verified against the local baseline — spend +$0.41 post-close
  restatement, all other checks exact)
- [x] Phase 0 — daily-pull workflow, baseline verifier, backfill snapshotter
- [ ] Phase 1 — baseline + decomposition
- [ ] Phase 2 — signal library seed
- [ ] Phase 3 — correlator + verdict engine
- [ ] Phase 4 — blind backtest (headline: Jun 25, 2026 verdict)
