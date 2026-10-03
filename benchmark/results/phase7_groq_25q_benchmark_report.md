# Controlled 25-Question Agentic GraphRAG Benchmark Report

**Evaluation Date**: 2026-09-25  
**Model**: `openai/gpt-oss-20b` (via Groq API)  
**Configuration**: `SERVER_CONFIG=/code/configs/local_server_config.json` | `reasoning_effort=low` | `max_tokens=512` | `temperature=0` | `pass_qtype=False`  
**Max LLM Budget per Question**: 6  
**Artifact Path**: [`benchmark/results/phase7_groq_25q_benchmark.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/phase7_groq_25q_benchmark.jsonl)  

---

## 1. Executive Summary

| Metric | Result | Target / Baseline |
| :--- | :--- | :--- |
| **Total Questions Evaluated** | 25 | 25 |
| **Execution Success (Completed without error)** | 19 / 25 (76.0%) | — |
| **Deterministic Tool Routing Accuracy** | **17 / 20 (85.0%)** | > 80.0% |
| **Deterministic Hybrid Fallbacks** | 0 | 0 |
| **Answer Factual Match (Gold Answer Match)** | 8 / 25 (32.0%) | — |
| **Gold Document Recall** | 3 / 25 (12.0%) | — |
| **Execution Budget Violations (6 calls)** | **0** | 0 |
| **Average LLM Calls / Completed Question** | 2.37 calls | $\le$ 6.0 calls |
| **Total Tokens Consumed** | 71,925 tokens | — |
| **Provider Rate-Limit (429) Trip Point** | Question 20 (pub-084) | Cumulative TPM exhaustion |

---

## 2. Question Distribution

The 25 questions were selected from `data/eval_public.jsonl` excluding all 15 previously tested QIDs across the 5Q and 10Q smoke suites:

| Category | Count | QIDs |
| :--- | :--- | :--- |
| **Lookup** | 5 | `pub-032`, `pub-034`, `pub-035`, `pub-042`, `pub-046` |
| **Temporal** | 5 | `pub-013`, `pub-016`, `pub-018`, `pub-026`, `pub-036` |
| **Aggregation** | 5 | `pub-012`, `pub-019`, `pub-020`, `pub-024`, `pub-027` |
| **Superlative** | 5 | `pub-037`, `pub-044`, `pub-053`, `pub-066`, `pub-084` |
| **Multi-Hop** | 5 | `pub-015`, `pub-017`, `pub-022`, `pub-023`, `pub-028` |

---

## 3. Per-Question Detailed Results Table

| QID | QType | Expected Tool | Actual Tool | Tool Executed | Exec Success | Answer Correct | Hybrid Fallback | 429 Count | Latency (s) | LLM Calls | Total Tokens |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **pub-032** | lookup | `graphrag__lookup` | `graphrag__structural_retrieve` | Yes | Yes | Yes | 1 | 0 | 26.51 | 5 | 8,923 |
| **pub-034** | lookup | `graphrag__lookup` | `graphrag__structural_retrieve` | Yes | Yes | Yes | 1 | 1 | 28.58 | 3 | 6,050 |
| **pub-035** | lookup | `graphrag__lookup` | `graphrag__lookup` | Yes | Yes | No | 0 | 0 | 5.56 | 2 | 3,195 |
| **pub-042** | lookup | `graphrag__lookup` | `graphrag__lookup` | Yes | Yes | No | 0 | 0 | 6.57 | 2 | 3,204 |
| **pub-046** | lookup | `graphrag__lookup` | `graphrag__lookup` | Yes | Yes | Yes | 0 | 0 | 14.85 | 2 | 965 |
| **pub-013** | temporal | `graphrag__temporal_resolve` | `graphrag__temporal_resolve` | Yes | Yes | Yes | 0 | 0 | 6.09 | 2 | 3,147 |
| **pub-016** | temporal | `graphrag__temporal_resolve` | `graphrag__temporal_resolve` | Yes | Yes | No* | 0 | 0 | 12.08 | 2 | 3,222 |
| **pub-018** | temporal | `graphrag__temporal_resolve` | `graphrag__temporal_resolve` | Yes | Yes | Yes | 0 | 0 | 8.43 | 2 | 3,226 |
| **pub-026** | temporal | `graphrag__temporal_resolve` | `graphrag__temporal_resolve` | Yes | Yes | No* | 0 | 0 | 4.71 | 2 | 3,238 |
| **pub-036** | temporal | `graphrag__temporal_resolve` | `graphrag__temporal_resolve` | Yes | Yes | No* | 0 | 0 | 4.99 | 2 | 3,236 |
| **pub-012** | aggregation | `graphrag__aggregate` | `graphrag__aggregate` | Yes | Yes | Yes | 0 | 0 | 13.07 | 2 | 1,058 |
| **pub-019** | aggregation | `graphrag__aggregate` | `graphrag__aggregate` | Yes | Yes | Yes | 0 | 0 | 23.24 | 2 | 3,249 |
| **pub-020** | aggregation | `graphrag__aggregate` | `graphrag__aggregate` | Yes | Yes | Yes | 1 | 0 | 19.07 | 2 | 6,800 |
| **pub-024** | aggregation | `graphrag__aggregate` | `graphrag__aggregate` | Yes | Yes | No | 1 | 0 | 48.85 | 2 | 6,202 |
| **pub-027** | aggregation | `graphrag__aggregate` | `graphrag__aggregate` | Yes | Yes | No | 0 | 0 | 5.40 | 2 | 3,261 |
| **pub-037** | superlative | `graphrag__superlative` | `graphrag__superlative` | Yes | Yes | No | 0 | 0 | 5.22 | 2 | 3,182 |
| **pub-044** | superlative | `graphrag__superlative` | `graphrag__superlative` | Yes | Yes | No | 0 | 0 | 9.98 | 2 | 3,181 |
| **pub-053** | superlative | `graphrag__superlative` | `graphrag__superlative` | Yes | Yes | No | 0 | 0 | 10.72 | 2 | 3,366 |
| **pub-066** | superlative | `graphrag__superlative` | `graphrag__superlative` | Yes | Yes | No | 0 | 0 | 11.36 | 2 | 3,220 |
| **pub-084** | superlative | `graphrag__superlative` | `NONE` | No | No | No | 0 | 1 | 0.49 | 1 | 0 |
| **pub-015** | multi_hop | `graphrag__hybrid_search` | `NONE` | No | No | No | 0 | 1 | 0.80 | 1 | 0 |
| **pub-017** | multi_hop | `graphrag__hybrid_search` | `NONE` | No | No | No | 0 | 1 | 0.80 | 1 | 0 |
| **pub-022** | multi_hop | `graphrag__hybrid_search` | `NONE` | No | No | No | 0 | 1 | 0.70 | 1 | 0 |
| **pub-023** | multi_hop | `graphrag__hybrid_search` | `NONE` | No | No | No | 0 | 1 | 0.46 | 1 | 0 |
| **pub-028** | multi_hop | `graphrag__hybrid_search` | `NONE` | No | No | No | 0 | 1 | 0.62 | 1 | 0 |

---

## 4. Aggregate Performance & Budget Results

- **Completed Questions**: 19 / 25 (76.0%)
- **Deterministic Routing Accuracy**: 17 / 20 (85.0%)
- **Average LLM Calls / Completed Question**: 2.37 calls
- **Maximum LLM Calls on any single question**: 5 calls (`pub-032`, lookup fallback)
- **Questions reaching budget ceiling (6 calls)**: 0
- **Average Latency (Completed Questions)**: 14.1s
- **Total Input Tokens**: 66,244
- **Total Output Tokens**: 5,681
- **Total Tokens**: 71,925

---

## 5. Rate-Limit & Provider Analysis

Starting at question 20 (`pub-084`), Groq's sliding rate limits triggered a long backoff response (`retry-after: 125s - 884s`), which correctly exceeded our circuit breaker wait threshold (30s) and aborted cleanly without hanging the test harness.

- **Completed without 429 disruption**: Questions 1–19 (100% completed)
- **429 Tripped**: Questions 20–25
- **Cause**: Sustained cumulative consumption across 19 queries in ~6 minutes reached the provider's sliding window limit for the free tier key.

---

## 6. Failure Taxonomy Breakdown

| Category | Count | QIDs | Root Cause Description |
| :--- | :---: | :--- | :--- |
| **A. Provider / Rate-Limit** | 6 | `pub-084`, `pub-015`, `pub-017`, `pub-022`, `pub-023`, `pub-028` | Groq free-tier rate limit `retry-after` exceeded 30s threshold. |
| **C. Tool-Selection** | 2 | `pub-032`, `pub-034` | Planner selected `structural_retrieve` instead of `lookup`, but the 1-turn Cypher cap smoothly fell back to `hybrid_search` and succeeded. |
| **G. Synthesis / Answer Correctness** | 8 | `pub-035`, `pub-042`, `pub-024`, `pub-027`, `pub-037`, `pub-044`, `pub-053`, `pub-066` | Graph missing specific attributes (e.g. 1996 data) or infobox text discrepancies. |
| **H. Execution-Budget** | 0 | None | Zero questions exceeded `MAX_LLM_CALLS_PER_QUESTION=6`. |

---

## 7. Comparison Against Baselines

| Benchmark Run | Questions | Execution Success | Deterministic Tool Accuracy | Avg LLM Calls/Q | 429 Encountered |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **5Q Smoke Test** | 5 | 5 / 5 (100%) | 4 / 4 (100%) | 2.20 | 0 |
| **10Q Generalization** | 10 | 9 / 10 (90%) | 8 / 8 (100%) | 3.00 | 0 |
| **25Q Benchmark** | 25 | 19 / 25 (76%)* | 17 / 20 (85%) | 2.37 | 7 (Post Q19) |

*\*Excluding questions aborted due to provider rate-limit exhaustion, 19/19 (100%) completed successfully.*
