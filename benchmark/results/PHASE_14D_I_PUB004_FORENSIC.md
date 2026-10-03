# PHASE 14D-I-A — PUB-004 RETRIEVAL FAILURE FORENSIC AUDIT

**PHASE 14D-I-A STATUS**: `PASS`

| Parameter | Value |
|---|---|
| **CLASSIFICATION** | `D` (EVALUATOR/TELEMETRY FALSE NEGATIVE) |
| **TOOL ACTUALLY EXECUTED** | `YES` |
| **EXACT TOOL** | `graphrag__superlative` |
| **EXACT ARGUMENTS** | `{"sport": "athletics", "games": "2008 Summer Olympics"}` |
| **TOOL RESULT** | `Athletics at the 2008 Summer Olympics – Men's marathon (95 competitors)` |
| **EVIDENCE PRESENT** | `YES` |
| **EVIDENCE PASSED TO SYNTHESIS** | `YES` |
| **REPLAN EVALUATED** | `YES` |
| **REPLAN COUNT** | `0` |
| **ANSWER SUPPORTED BY TOOL RESULT** | `YES` |
| **RETRIEVAL FAILURE** | `FALSE NEGATIVE` |
| **RETRY ARCHITECTURE** | `PASS` |
| **BUDGET** | `PASS` |
| **PRODUCTION FILES MODIFIED** | `0` |
| **API CALLS** | `0` |
| **LIVE BENCHMARKS RUN** | `0` |

---

## Final Diagnosis

1. **Root Cause of `RETRIEVAL: FAIL` Label**:
   In `scratch/run_phase14d_i_pub004.py`, line 94 filtered tool traces using:
   `if step.get("kind") == "retrieval":`
   However, in `agentic_executor.py`, traces preserve `step.kind`, which for deterministic tools like `graphrag__superlative` is assigned `"unstructured"` or `"deterministic"`, NOT `"retrieval"`.
   As a consequence, the test script skipped inspecting the output of `graphrag__superlative` and set `evidence_context_returned` to `false` and `retrieval_status` to `FAIL`.

2. **Actual System Execution Evidence**:
   - `graphrag__superlative` was invoked with `{"sport": "athletics", "games": "2008 Summer Olympics"}`.
   - It executed the deterministic GSQL superlative query against TigerGraph and returned valid evidence: **Athletics at the 2008 Summer Olympics – Men's marathon** with **95 competitors**.
   - The result was populated into `StepResult` context and passed directly to synthesis.
   - Replan safety evaluated `has_context(results) == True`, correctly deciding `0` replans were needed.
   - Synthesis generated the exact gold answer in **10.098 seconds**:
     > "According to the provided corpus, the athletics event at the 2008 Summer Olympics with the highest number of competitors was Athletics at the 2008 Summer Olympics – Men's marathon, which had 95 competitors."

3. **Phase 14D-H Architectural Verification**:
   - `logical_llm_calls`: `3` ($\le 6$)
   - `provider_http_attempts`: `3` ($\le 2$ per logical call)
   - `provider_retries`: `0` ($\le 1$)
   - `provider_failovers`: `0`
   - `replans`: `0` ($\le 1$)
   - `agent_steps`: `1` ($\le 5$)

---

## Next Action
Fix the runner script step filtering condition to check `step.get("kind") in ("retrieval", "unstructured", "deterministic", "superlative")` and proceed to authorization for the 5Q smoke benchmark.
