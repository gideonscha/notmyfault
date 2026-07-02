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

Pulls land in `data/meta/` (gitignored) as CSV + parquet:
`account_daily`, `campaign_daily`, `account_daily_placement`, `account_daily_demo`.

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
- [ ] Phase 0 — 12-month data pull **(blocked: META_ACCESS_TOKEN must be added to `.env` from a machine that has it — this remote session had no access to the magic-portraits-ads skill's credentials)**
- [ ] Phase 1 — baseline + decomposition
- [ ] Phase 2 — signal library seed
- [ ] Phase 3 — correlator + verdict engine
- [ ] Phase 4 — blind backtest (headline: Jun 25, 2026 verdict)
