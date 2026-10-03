# Three-Way Metrics Reconciliation

## 1. Purpose

This document provides the authoritative, evidence-backed metrics reconciliation comparing **Classical RAG**, **GraphRAG (Hybrid Graph Search)**, and **Agentic GraphRAG** for the TigerGraph Agentic GraphRAG project submission.

The objective is to establish a single, auditable source of truth across all three system paradigms evaluated on the official 100-question visible benchmark dataset (`data/eval_public.jsonl`).

---

## 2. Benchmark Comparability

All three system paradigms were evaluated on the identical 100-question public dataset (`data/eval_public.jsonl`).

### Dataset Integrity Verification
- **File Path:** `data/eval_public.jsonl`
- **Question Count:** Exactly 100 questions
- **SHA-256 Hash:** `ABDDB7D18A6D8ED908F514a7e560fe4950EBE479EBB2CDB75A7456887C10C6E5`

### Evaluation Contract & Metrics Definition
- **Normalized Accuracy:** Evaluated using the official unified evaluator (`benchmark/unified_evaluator.py`), applying string normalization (case-folding, punctuation strip, CamelCase word splitting, unicode normalization) and regex/token-set match against ground-truth labels.
- **HTTP Success Rate:** Percentage of benchmark requests completing without network errors, HTTP failure codes, or unhandled exceptions.
- **Evidence / Gold Recall:** Percentage of questions where the retrieved context contained the exact gold evidence/entity necessary to produce the correct answer.

---

## 3. Authoritative Results

The table below reconciles the authoritative benchmark results across all three paradigms evaluated on the full 100-question dataset under the normalized evaluation contract.

| Metric | RAG | GraphRAG | Agentic GraphRAG |
|---|---:|---:|---:|
| **Questions** | 100 | 100 | 100 |
| **HTTP Success** | 100/100 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) |
| **Accuracy (Normalized)** | 19/100 (19.0%) | 20/100 (20.0%) | **95/100 (95.0%)** |
| **Evidence / Gold Recall** | 3/100 (3.0%) | 16/100 (16.0%) | **95/100 (95.0%)** |
| **Total Runtime** | ~1,128.9 s | ~3,504.3 s | **3,943.0 s** (~65.7 min) |
| **Avg Latency** | 11.29 s (11,289 ms) | 35.04 s (35,043 ms) | **39.43 s** (39,430 ms) |
| **Token Usage (Avg / Total)** | 8,617.17 / ~861.7k tokens | 1,103.30 / ~110.3k tokens | **7,718.01 / ~771.8k tokens** |
| **LLM Calls / Question** | 1.00 call/q | 1.00 call/q | **3.04 calls/q** |
| **Retrieval / Tool Usage** | Vector Similarity Search (`top_k=5`) | Seed Vector + 1-Hop Graph Expansion | Deterministic Olympic GSQL Tools + Hybrid Search |
| **Cost** | $0.00 (Local / Open Weights) | $0.00 (Local / Open Weights) | **$0.00** (AIRouter Free Tier / Open Weights) |
| **Model** | Qwen-3 Embedding 0.6B + LLM | Qwen-3 Embedding 0.6B + TigerGraph + LLM | **AIRouter `openai/gpt-oss-20b` + TigerGraph MCP** |
| **Dataset** | `data/eval_public.jsonl` (100Q) | `data/eval_public.jsonl` (100Q) | **`data/eval_public.jsonl` (100Q)** |

---

## 4. RAG Result Provenance

The Classical RAG benchmark metrics are sourced from the Phase 3 Baseline execution.

- **Primary Source File:** [`benchmark/results/rag_baseline_summary.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/rag_baseline_summary.json)
- **Detailed JSONL Artifact:** [`benchmark/results/phase3_qwen_100_benchmark.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/phase3_qwen_100_benchmark.jsonl)
- **Normalized Artifact:** [`benchmark/results/rag_baseline_normalized.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/rag_baseline_normalized.jsonl)
- **Reconciliation Matrix:** [`benchmark/results/three_way_comparison.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/three_way_comparison.json)

### Breakdown by Question Type (RAG)
- **Aggregation (21 questions):** 85.71% accuracy (18/21)
- **Lookup (19 questions):** 5.26% accuracy (1/19)
- **Temporal (22 questions):** 0.0% accuracy (0/22)
- **Superlative (10 questions):** 0.0% accuracy (0/10)
- **Multi-Hop (28 questions):** 0.0% accuracy (0/28)
- **Primary Failure Mechanism:** High distractor chunk noise and complete inability to perform multi-hop entity traversal or temporal link resolution.

---

## 5. GraphRAG Result Provenance

The GraphRAG (Hybrid Graph Search) benchmark metrics are sourced from the Phase 5 Baseline execution.

- **Primary Source File:** [`benchmark/results/graphrag_baseline_summary.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/graphrag_baseline_summary.json)
- **Detailed JSONL Artifact:** [`benchmark/results/phase5_qwen_hybrid_100_benchmark.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/phase5_qwen_hybrid_100_benchmark.jsonl)
- **Normalized Artifact:** [`benchmark/results/graphrag_baseline_normalized.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/graphrag_baseline_normalized.jsonl)
- **Reconciliation Matrix:** [`benchmark/results/three_way_comparison.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/three_way_comparison.json)

### Breakdown by Question Type (GraphRAG)
- **Aggregation (21 questions):** 85.71% accuracy (18/21)
- **Lookup (19 questions):** 10.53% accuracy (2/19)
- **Temporal (22 questions):** 0.0% accuracy (0/22)
- **Superlative (10 questions):** 0.0% accuracy (0/10)
- **Multi-Hop (28 questions):** 0.0% accuracy (0/28)
- **Primary Failure Mechanism:** 73 zero-context dropouts (73.0% failure rate) caused by seed vector chunks lacking outgoing `DOCUMENT_HAS_EVENT` graph traversal edges in the graph schema.

---

## 6. Agentic GraphRAG Result Provenance

The final Agentic GraphRAG benchmark metrics are sourced from the Phase 15 Final Production Benchmark run completed on October 2, 2026.

- **Primary Summary File:** [`benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK_SUMMARY.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK_SUMMARY.json)
- **Primary Report File:** [`benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK_REPORT.md`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK_REPORT.md)
- **Detailed JSONL Artifact:** [`benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK.jsonl)
- **Per-QID Trace File:** [`benchmark/results/FINAL_100Q_AGENTIC_QID_TRACE.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_100Q_AGENTIC_QID_TRACE.csv)

### Breakdown by Question Type (Final Agentic GraphRAG)
- **Aggregation (21 questions):** **100.0% accuracy** (21/21) | Mean Latency: 26.51 s
- **Lookup (19 questions):** **100.0% accuracy** (19/19) | Mean Latency: 44.94 s
- **Temporal (22 questions):** **100.0% accuracy** (22/22) | Mean Latency: 43.52 s
- **Superlative (10 questions):** **100.0% accuracy** (10/10) | Mean Latency: 22.46 s
- **Multi-Hop (28 questions):** **82.1% accuracy** (23/28) | Mean Latency: 48.22 s
- **Overall Total:** **95/100 (95.0%) Normalized Accuracy**, **100/100 (100.0%) HTTP Success**, **3,943.0s total runtime**.

---

## 7. Historical vs Final Results

During project evolution, several intermediate benchmarks were recorded under different evaluator configurations or model backends. The table below clarifies historical development runs versus the authoritative final benchmark.

| Phase / Artifact | Question Scope | Agentic Accuracy | Key Difference / Context | Authoritative Status |
|---|:---:|:---:|---|:---:|
| **Phase 7 (Standard Baseline)** | 100Q | 76.0% (76/100) | Initial agentic engine with 18 query timeouts. | Superseded by Phase 14 |
| **Phase 11B (Authenticity Run)** | 100Q | 87.0% (87/100) | Multi-provider failover backend (Groq + OpenRouter + FreeLLM). | Superseded by Phase 14 |
| **Phase 14 Baseline** | 100Q | 88.0% (88/100) | AIRouter `openai/gpt-oss-20b` baseline before Phase 15 multi-hop repairs. | Pre-Phase 15 Baseline |
| **Phase 15 Final Benchmark** | **100Q** | **95.0% (95/100)** | **Final production Agentic GraphRAG stack with output salvage & multi-event disambiguation.** | **OFFICIAL FINAL SUBMISSION RESULT** |

### Explanation of Metric Variations in Secondary Logs
1. **Unnormalized Strict Match vs Normalized Accuracy:** In early unnormalized evaluation logs (`final_three_way_summary.json`), RAG and GraphRAG showed 0.0% strict exact match because their outputs were conversational prose while gold labels contained unspaced strings. Under the official unified evaluator (`benchmark/unified_evaluator.py`), normalized accuracy is **19.0% for RAG**, **20.0% for GraphRAG**, **88.0% for Pre-Phase 15 Agentic**, and **95.0% for Final Agentic GraphRAG**.
2. **Pilot Tables in Documentation:** Early progress documents referenced preliminary pilot estimates (e.g. 43% for RAG or 64% for GraphRAG on a 15-question pilot subset). These pilots were superseded by the complete 100-question benchmark runs.

---

## 8. Metric Limitations

1. **Strict Exact Match Limitations:** Strict exact string matching yields 0.0% across all structured prose responses when gold dataset targets contain unspaced concatenated strings (e.g., `"Dani KingLaura TrottJoanna Rowsell"`). Normalized evaluation is required to evaluate semantic correctness fairly.
2. **Cost Calculation:** All benchmark evaluations utilized local open-weights embedding models (Qwen-3 0.6B) and free-tier/open API endpoints (AIRouter). Financial cost is reported as $0.00.
3. **Execution Environment Differences:** Latencies reflect execution within a Docker container environment connected to TigerGraph via REST/MCP protocols.

---

## 9. Final Submission Numbers

For official hackathon submission forms, presentations, and executive summaries, use **only** the following consolidated metrics:

- **Classical RAG Accuracy:** **19.0%** (19/100 normalized match, 100/100 HTTP success)
- **GraphRAG Accuracy:** **20.0%** (20/100 normalized match, 100/100 HTTP success)
- **Agentic GraphRAG Accuracy:** **95.0%** (95/100 normalized match, 100/100 HTTP success)
- **Agentic Accuracy Gain over RAG:** **+76 percentage points** (19% → 95%, **5.0x improvement**)
- **Agentic Accuracy Gain over GraphRAG:** **+75 percentage points** (20% → 95%, **4.75x improvement**)
- **Agentic Phase 15 Gain:** **+7 percentage points** (88% → 95%)
- **Non-Multi-Hop Accuracy:** **72/72 (100.0%)** across Aggregation, Temporal, Superlative, and Lookup
- **Multi-Hop Accuracy:** **23/28 (82.1%)**
- **Total Agentic Runtime:** **3,943.0 seconds** (~65.7 minutes across 100 questions)
- **Mean Latency per Question:** **39.43 seconds**

---

## 10. Source Artifacts

The following repository files serve as the authoritative evidence for all numbers in this report:

1. `data/eval_public.jsonl` (SHA-256: `abddb7d18a6d8ed908f514a7e560fe4950ebe479ebb2cdb75a7456887c10c6e5`)
2. `benchmark/results/rag_baseline_summary.json`
3. `benchmark/results/phase3_qwen_100_benchmark.jsonl`
4. `benchmark/results/graphrag_baseline_summary.json`
5. `benchmark/results/phase5_qwen_hybrid_100_benchmark.jsonl`
6. `benchmark/results/three_way_comparison.json`
7. `benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK_SUMMARY.json`
8. `benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK_REPORT.md`
9. `benchmark/results/FINAL_100Q_AGENTIC_BENCHMARK.jsonl`
10. `benchmark/results/FINAL_100Q_AGENTIC_QID_TRACE.csv`
11. `benchmark/unified_evaluator.py`
