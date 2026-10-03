# PHASE 14D-L-A — 25Q QUESTION SET PROVENANCE CHECK REPORT

**QUESTION SET VERDICT**: `NEEDS CLARIFICATION`

| Parameter | Value |
|---|---|
| **API CALLS** | `0` |
| **LIVE QUESTIONS** | `0` |
| **PRODUCTION FILES MODIFIED** | `0` |
| **RUNNER QID COUNT** | `25/25` |
| **DUPLICATES FOUND** | `NO` |
| **MISSING QIDS** | `NO` |
| **OVERLAP WITH PHASE 14D 5Q** | `5 QIDs (pub-001 through pub-005)` |
| **ALTERNATIVE STRATIFIED 25Q OVERLAP** | `0 QIDs` |

---

## Detailed Provenance Analysis

1. **Exact 25 QIDs Selected by `run_phase14d_l_25q_pilot.py`**:
   `pub-001`, `pub-002`, `pub-003`, `pub-004`, `pub-005`, `pub-006`, `pub-007`, `pub-008`, `pub-009`, `pub-010`, `pub-011`, `pub-012`, `pub-013`, `pub-014`, `pub-015`, `pub-016`, `pub-017`, `pub-018`, `pub-019`, `pub-020`, `pub-021`, `pub-022`, `pub-023`, `pub-024`, `pub-025`.

2. **Prior Phase 14D 5Q Overlap Check**:
   - `pub-001` through `pub-005` were executed during Phase 14D Gate 10 (5Q smoke test).
   - `pub-004` was also executed during Phase 14D-I (1Q validation).
   - Thus, **5 out of 25 QIDs** overlap with prior Phase 14D live tests.

3. **Methodology Options**:
   - **Option A (Sequential 25Q)**: `pub-001` – `pub-025` (matches Phase 13 Gate 7 methodology). 5 QIDs overlap with 5Q smoke test.
   - **Option B (Stratified 25Q)**: `SELECTED_25_QIDS` from `scratch/run_25q_benchmark.py` (5 Lookup, 5 Temporal, 5 Aggregation, 5 Superlative, 5 Multi-hop). **0 QIDs overlap** with Phase 14D 5Q.

4. **Duplication & Completeness**:
   - 0 duplicate QIDs.
   - 0 missing QIDs.
   - 25 unique QIDs total.
