# PHASE 14D-L-B — STRATIFIED FRESH 25Q SELECTION REPORT

**STATUS**: `PASS`

| Parameter | Value |
|---|---|
| **QUESTION SET** | `SELECTED_25_QIDS` (from `scratch/run_25q_benchmark.py`) |
| **COUNT** | `25` |
| **UNIQUE QIDS** | `25/25` |
| **DISTRIBUTION** | `5 Lookup / 5 Temporal / 5 Aggregation / 5 Superlative / 5 Multi-hop` |
| **OVERLAP WITH PHASE 14D 5Q** | `0` |
| **OVERLAP WITH PHASE 13 25Q BENCHMARK** | `11` (`pub-012`, `pub-013`, `pub-015`, `pub-016`, `pub-017`, `pub-018`, `pub-019`, `pub-020`, `pub-022`, `pub-023`, `pub-024`) |
| **OVERLAP WITH PHASE 12 100Q BENCHMARK** | `25` (All 25 QIDs drawn from canonical 100Q dataset) |
| **API CALLS** | `0` |
| **LIVE QUESTIONS** | `0` |
| **PRODUCTION FILES MODIFIED** | `0` |
| **PHASE 12 MODIFIED** | `NO` |
| **PHASE 13 MODIFIED** | `NO` |

---

## Detailed Question Selection Breakdown

- **Lookup (5)**: `pub-032`, `pub-034`, `pub-035`, `pub-042`, `pub-046`
- **Temporal (5)**: `pub-013`, `pub-016`, `pub-018`, `pub-026`, `pub-036`
- **Aggregation (5)**: `pub-012`, `pub-019`, `pub-020`, `pub-024`, `pub-027`
- **Superlative (5)**: `pub-037`, `pub-044`, `pub-053`, `pub-066`, `pub-084`
- **Multi-hop (5)**: `pub-015`, `pub-017`, `pub-022`, `pub-023`, `pub-028`

## Verification Summary
1. `run_phase14d_l_25q_pilot.py` question selection updated to load `SELECTED_25_QIDS`.
2. Python compilation check: **PASS** (0 syntax errors).
3. 0 live API calls or benchmark questions executed (**PASS**).
4. 0 production Agentic/RAG files modified (**PASS**).
