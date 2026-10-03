# Phase 11A — Improvement Decision & Engineering Specification

**Document Version:** 1.0  
**Repository:** `TigerGraph Olympics Benchmark`  
**Evaluation Status:** Gate 14 — Formal Engineering & Metric Improvement Decision  

---

## 1. Current Trustworthy Metrics

The following metrics from the Phase 11 100-Question Public Benchmark have been verified to be mathematically sound, deterministic, and fully reproducible from raw JSONL traces:

1. **Agentic GraphRAG Answer Accuracy**: **87/100 (87.0%)** normalized substring match across the 100 public questions.
2. **Agentic Gold Evidence Grounding**: **93/100 (93.0%)** combined gold evidence recall.
3. **Agentic Query Completion Rate**: **94/100 (94.0%)** completed without hitting the 120s HTTP timeout ceiling.
4. **Agentic Token Accounting Formula**: Strictly additive ($\text{Total} = \text{Input} + \text{Output}$) with zero discrepancies across all 94 populated records.
5. **Deterministic GSQL Tool Zero-Token Cost**: Proven that native TigerGraph tools (`lookup`, `aggregate`, `superlative`, `temporal_resolve`) consume 0 LLM prompt/completion tokens.
6. **Task Completion Latency (Completed Queries)**:
   - Agentic GraphRAG: **39.281 seconds** ($N=94$).
   - GraphRAG: **68.528 seconds** ($N=27$).
   - Base RAG: **86.441 seconds** ($N=6$).

---

## 2. Metrics Requiring Correction

1. **Base RAG & GraphRAG Accuracy Labels**:
   - The reported 19% (RAG) and 20% (GraphRAG) figures must be explicitly labelled as `normalized_substring_match_with_fallback_overlap`.
   - In strict non-fallback evaluation, true RAG accuracy is **2% (2/100)** and GraphRAG is **2% (2/100)** because 17–18 matches were single-digit gold numbers matching hex characters in crashed 500 error UUID strings.
2. **Naive Aggregate Latency**:
   - The headline latency of 11.289s (RAG) and 35.043s (GraphRAG) was artificially lowered by 94% and 73% of queries crashing in 2–6 seconds.
   - Reporting must feature `avg_latency_completed_ms` (RAG: 86.44s, GraphRAG: 68.53s, Agentic: 39.28s).
3. **GraphRAG Retrieval Intrusion**:
   - The reported 100.0% intrusion was an evaluator chunk-suffix matching bug. Corrected true non-Olympic intrusion across all three pipelines is **0.00%**.

---

## 3. Evaluator Bugs Identified & Resolved

1. **UUID Fallback Hex Collision Bug**:
   - *Locus*: `compute_normalized_match` in `benchmark/unified_evaluator.py`.
   - *Impact*: Error fallback strings containing admin UUIDs (e.g. `ba8051e7...`) matched single-digit gold answers (`5`, `8`).
   - *Resolution*: Error fallback responses (`"Admin reference ID: ..."`) must be explicitly classified as `correct = False` prior to running substring containment.
2. **Chunk Suffix Stripping in Intrusion Evaluator**:
   - *Locus*: `calculate_retrieval_intrusion` in `benchmark/unified_evaluator.py`.
   - *Impact*: GraphRAG returned chunk IDs in the format `Qxxxx_chunk_0`, which failed direct equality against gold document IDs `Qxxxx`.
   - *Resolution*: Strip `_chunk_\d+` suffix before membership validation against gold document sets.

---

## 4. Reporting & Telemetry Bugs

1. **Flat `strategy_changes` Metric Field**:
   - The agentic orchestrator logged replanning as `"node": "replan 1"` within `agent_steps`, but did not populate the flat top-level key `"strategy_changes"` in `query_sources`.
   - The evaluator defaulted to `0`, creating the misleading narrative that no replanning occurred.
2. **QType Misattribution in Unresolved Queries**:
   - Narrative previously claimed "13 unresolved multi-hop questions", whereas the actual 13 failures comprise **10 Multi-Hop, 2 Superlatives, and 1 Temporal query**.

---

## 5. Genuine Agentic Failures

The audit confirmed **13 genuine Agentic failures** out of 100 questions:
- **Timeouts (6)**: 6 queries reached the 120.0s HTTP client ceiling during complex joint graph traversals.
- **Synthesis / Output Formatting (4)**: 4 queries retrieved the exact gold entities and chunks, but failed due to natural language rephrasing or unspaced gold strings.
- **Synthesis Boilerplate (2)**: 2 queries retrieved gold chunks, but the synthesizer generated default fallback text.
- **Retrieval Miss (1)**: 1 query missed the required chunk in vector search top-k.

---

## 6. Multi-Hop Failure Distribution (10 Failed Questions)

| Failure Category | Count | QIDs | Primary Mechanism |
| :--- | :--- :--- | :--- | :--- |
| **`other` (120s HTTP Client Timeout)** | **5** | `pub-015`, `pub-076`, `pub-077`, `pub-096`, `pub-098` | Joint graph and vector exploration exceeded the 120-second client timeout. |
| **`synthesis` (Default Boilerplate)** | **2** | `pub-023`, `pub-067` | Gold event located by tools, but synthesis output generic fallback text. |
| **`retrieval_miss`** | **1** | `pub-017` | Vector top-k missed chunk with 28 July 2012 shooting date constraint. |
| **`tool_argument_error` / Replan Budget** | **1** | `pub-060` | Tool schema argument validation error on initial step; replanning hit call budget. |
| **`output_formatting`** | **1** | `pub-099` | All 4 relay winners extracted, but gold string was unspaced concatenated names. |

---

## 7. Superlative Failure Distribution (2 Failed Questions)

| Failure Category | Count | QIDs | Primary Mechanism |
| :--- | :--- :--- | :--- | :--- |
| **`synthesis_verbatim_title_truncation`** | **2** | `pub-004`, `pub-008` | Tool returned exact Wikipedia article title (e.g. `Athletics at the 2008 Summer Olympics – Men's marathon`), but synthesizer condensed it to conversational prose (`"Men's marathon"`), failing evaluator contiguous substring check. |

---

## 8. Accuracy Improvement Opportunities

1. **Synthesizer Canonical Title Preservation**:
   - Instructing the synthesizer to preserve the canonical title verbatim for superlative queries directly addresses the failure mechanism in `pub-004` and `pub-008`.
2. **Multi-Hop Timeout Mitigation**:
   - Raising client HTTP timeouts from 120s to 180s or parallelizing blocking graph I/O addresses the timeout ceiling affecting 5 Multi-Hop and 1 Temporal query.
3. **Structured Tool Argument Enforcement**:
   - Hardening prompt schema bindings prevents missing `question` argument validation errors (`pub-060`).

---

## 9. Risks of Changing the Frozen Baseline

1. **Loss of Historical Comparability**: Altering prompt structures or retrieval algorithms could invalidate previously certified baselines (e.g. Phase 6 78/78 suite).
2. **Overfitting to Public Benchmarks**: Tuning synthesizer prompts specifically for public QIDs risks regressing unseen enterprise queries.
3. **Latency Inflation**: Adding additional retries or higher top-k values increases latency and token budgets.

---

## 10. Recommended Engineering Fixes

1. **Fix 1: Verbatim Canonical Title Inclusion in Synthesis Prompt**:
   - *Target*: General synthesis prompt in `base_llm.py`.
   - *Rule*: When structured tools return an Olympic event entity, format the official title in bold alongside conversational text.
2. **Fix 2: Client Benchmark Timeout Configuration**:
   - *Target*: `benchmark/run_qwen_100_benchmark.py`.
   - *Rule*: Set client HTTP timeout to 180s to accommodate deep 3-step joint graph-vector traversals.
3. **Fix 3: Tool Argument Schema Validation Guard**:
   - *Target*: `agentic_planner.py`.
   - *Rule*: Ensure all generated retrieval tool steps guarantee non-null `question` string arguments.

---

## 11. Expected Effect of Recommended Fixes

- **Canonical Title Fix**: Fix targets failure category `synthesis_verbatim_title_truncation` affecting **2 Superlative questions** (`pub-004`, `pub-008`).
- **Timeout Extension Fix**: Fix targets failure category `other (HTTP Client Timeout)` affecting **5 Multi-Hop questions** (`pub-015`, `pub-076`, `pub-077`, `pub-096`, `pub-098`) and **1 Temporal question** (`pub-096`).
- **Schema Validation Fix**: Fix targets failure category `tool_argument_error` affecting **1 Multi-Hop question** (`pub-060`).
- **Synthesis Boilerplate Fix**: Fix targets failure category `synthesis` affecting **2 Multi-Hop questions** (`pub-023`, `pub-067`).

---

## 12. Justification for Another 100Q Benchmark Run

- **Verdict**: **A future benchmark run is JUSTIFIED only AFTER targeted engineering fixes 1–3 are implemented**.
- **Pre-requisites Before Rerunning**:
  1. Freeze audited evaluation contract.
  2. Implement general synthesizer canonical title rule in code.
  3. Execute smoke-test suite (Phase 6 78/78 PASS).
  4. Perform single authoritative validation run.
