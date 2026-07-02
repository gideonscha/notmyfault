# NOTMYFAULT — Operating Rules

Meta Performance Exculpation Engine. Answers one question for an advertiser with a
sudden multi-day CPA/ROAS deterioration: **was it something you did, or something in
the environment?** Output is a verdict report — classified, evidence-backed,
confidence-scored. The engine must be equally willing to convict the advertiser as to
exonerate them; credibility is the product.

## Verdict classes

- `REPORTING_ARTIFACT` — not a real drop (attribution lag, CAPI health, window changes). **Check FIRST — cheapest verdict.**
- `INTERNAL_FUNNEL` — site/checkout/pricing change broke conversion
- `INTERNAL_ADS` — advertiser account changes (budget moves, edits, learning resets)
- `EXTERNAL_AUCTION` — CPM inflation / competitive pressure
- `EXTERNAL_PLATFORM` — Meta-side: algorithm rollout, delivery bug, outage, placement shift
- `EXTERNAL_DEMAND` — macro/attention/calendar demand suppression
- `MIXED` — quantified split between causes

Decomposition: **CPA = CPM ÷ (CTR × CVR)**. Each component implicates a different layer
(see §4 of the kickoff brief, mirrored in `engine/decompose.py`).

## Rules

1. **Recon first, always.** Read existing data/files before writing or modifying anything.
2. **Secrets discipline:** all keys in `.env` (local) or environment variables /
   GitHub Actions Secrets (cloud, CI) — never in code, never echoed, never in
   URLs (Bearer header only). Use
   `printf '%s'` patterns for any secret handling. The Meta token should be a
   system-user token scoped read-only to `ads_read`. `.env` is gitignored — verify
   before every commit.
3. **Human-in-the-loop:** the engine is read-only against Meta. It never modifies
   campaigns, budgets, or account settings. Analysis only.
4. **No guessed facts in the signal library.** Every event record in
   `signals/library.json` requires a verified `source_url` and date before
   `verified: true`. Unverified records are excluded from verdicts.
5. **Anti-horoscope rule:** no external signal appears in a verdict without a
   quantified, dated, account-specific effect estimate backtested against the
   account's own history — or an explicit "correlation only, coefficient unknown"
   flag. "There was news that week" is never evidence on its own.
6. **Verify, don't self-certify:** after each phase, output the verification
   command/result, not a claim of success.
7. **Notion Command Center:** silent upsert to Project Tracker at session end
   (project: NotMyFault / Meta Exculpation Engine).

## Data-layer boundaries

- **Meta Marketing API (direct, `engine/fetch_meta.py`)** — the runtime data layer.
  Bulk paginated pulls to files in `data/meta/`, deterministic re-runs.
  **Cloud caveat:** Claude Code cloud containers cannot reach
  `graph.facebook.com` (egress policy 403). The pull runs on GitHub Actions
  instead (`.github/workflows/daily-pull.yml`, 06:00 UTC daily, secrets from
  Actions Secrets), which commits refreshed data back to the repo.
- **`data/meta/` lives in-repo for now** (CSV + parquet + dated
  `backfill_observations/` snapshots) so cloud sessions are self-sufficient
  without Meta API access. Revisit if size or privacy becomes a concern.
- **Meta MCP** — development and verification only: recon, spot-checking engine
  numbers against a second source, Ad Library exploration. Never part of the
  runtime pipeline.
- Baseline is the account's **own** trailing 90-day history, day-of-week and
  month-position adjusted. No peer network.

## Layout

See §3 of the kickoff brief: `engine/` (baseline, decompose, correlate, verdict,
fetch), `signals/` (library.json + raw sources), `backtest/` (labeled incidents +
runner), `data/` (committed Meta pulls — see data-layer boundaries), `reports/`
(generated verdicts).
