"""Phase 1 — CPA decomposition (brief §4). NOT YET IMPLEMENTED.

CPA = CPM / (CTR * CVR), CVR measured link-click -> purchase with
checkout-entry as intermediate node when site data is available.

| Pattern                    | Primary suspect                       |
|----------------------------|---------------------------------------|
| CPM up, CTR/CVR flat       | EXTERNAL_AUCTION                      |
| CTR down, CPM flat         | creative fatigue OR delivery shift    |
| CVR down, upstream flat    | INTERNAL_FUNNEL OR EXTERNAL_DEMAND    |
| all bad, recovers on repull| REPORTING_ARTIFACT (check FIRST)      |
"""

raise NotImplementedError("Phase 1 — implement after Phase 0 data pull is verified")
