# Confidence calibration note — Phase 4

Sample: 2 resolvable incidents + 1 unresolved live case. n=2 supports only ordinal checks, not calibration curves.

| verdict | conf | outcome |
|---|---|---|
| mar13 INTERNAL_ADS (learning reset) | 0.80 | correct |
| may24 INTERNAL_FUNNEL (instrumentation) | 0.92 | correct |
| jun25 MIXED 59/41/0 | 0.55 | unresolved by design — confidence reflects the unsplittable internal pair, not doubt about locus |

Observations:
1. Both resolvable incidents were decided by cascade rules added during Phase 4 prep (R1b pause-resume;
   R0 instrumentation upgrade), before unsealing but with labels present in-repo all session. PROCEDURAL
   blindness only — n=2 cannot distinguish principled rules from overfitting. Treat 0.80/0.92 as
   upper bounds until out-of-sample incidents accrue.
2. The Phase 3 sweep's UNEXPLAINED confidences (semantics: confidence that known signals do NOT explain)
   are untested by this backtest — no labeled negative exists.
3. Bands (HIGH/MED/LOW) should be read ordinally. Recommendation: freeze thresholds now; re-calibrate
   after 5+ labeled incidents; log every future verdict-vs-resolution pair into incidents.json as it
   resolves (the live case will become datapoint 3 when the advertiser confirms/refutes via the
   recommended follow-ups).
4. Watch-item: INTERNAL_ADS spend-window verdicts (0.75-0.85) rely on activity presence in a 72h
   lookback; base rate is high in an actively-managed account. The May 26-27 counterexample (no
   activity -> UNEXPLAINED) shows discrimination, but a shuffle test (random windows vs activity
   presence) would quantify the false-positive rate — recommended before trusting 0.85.
