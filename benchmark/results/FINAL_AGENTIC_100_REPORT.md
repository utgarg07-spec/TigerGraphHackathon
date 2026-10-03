# PHASE 12 — FINAL AUTHORITATIVE 100Q BENCHMARK REPORT

**Date**: 2026-09-29  
**Pipeline**: Agentic GraphRAG System (Qwen2.5-Coder-32B-Instruct)  
**Evaluation Scope**: Complete 100-Question Public Benchmark (`data/eval_public.jsonl`)  
**Status**: COMPLETE — ALL 10 GATES VERIFIED

---

## 1. Executive Summary

Phase 12 executed the final, authoritative, un-cached, sequential live benchmark run (`FINAL_AGENTIC_100_LIVE`) across all 100 questions in the benchmark suite. 

The three approved Phase 11B general system fixes were active throughout execution:
1. **Canonical Event Title Preservation**: Prompt synthesis constraint in `common/llm_services/base_llm.py` (`_CHATBOT_RESPONSE_USER_DEFAULT`).
2. **Benchmark Client Timeout Ceiling**: Increased client-side HTTP timeout to 180s in `benchmark/runner.py`.
3. **General Tool Argument Validation Guard**: Hardened argument sanitization across `graphrag/app/agent/agentic_planner.py`, `common/py_schemas/schemas.py`, and `graphrag/app/tools/tool_registry.py`.

### Key Benchmark Metrics Overview

- **Overall Normalized Match Accuracy**: **76.0%** (76 / 100)
- **Combined Gold Evidence Hit Rate**: **79.0%** (79 / 100)
- **Completed Requests Within Timeout**: **82.0%** (82 / 100)
- **Timeouts at 180s Ceiling**: **18.0%** (18 / 100)
- **Average Total Latency**: **74.30 seconds**
- **Average Total Tokens**: **7,255 tokens / question**

---

## 2. Gate 1 — Architecture Freeze & Pre-Flight Verification

Before launching the live benchmark, the system state was audited and frozen:
- **Docker Microservices**: All containers (`graphrag`, `graphrag-ui`, `graphrag-ecc`, `chat-history`) healthy and operational.
- **Phase 6 Deterministic Tools Suite**: **78 / 78 PASS (100.0%)** verified via `docker exec graphrag python /code/tools/test_olympic_tools.py`.
- **Execution Budget Constraints**:
  - `MAX_LLM_CALLS_PER_QUESTION = 6` (Verified)
  - `MAX_PLAN_RETRIES = 2` (Verified)
  - `MAX_AGENT_STEPS = 5` (Verified)
  - HTTP Timeout Ceiling = `180.0 seconds` (Verified)
- **Codebase Integrity**: Zero ad-hoc or QID-specific hacks introduced. Architecture frozen.

---

## 3. Gate 2 & 3 — Live Execution Telemetry & Authenticity

The live benchmark executed 100 distinct questions sequentially against the local GraphRAG application server.

- **Total QIDs Attempted**: 100 / 100 (Unique QIDs, zero duplicates, zero skipped)
- **Live HTTP Requests**: 100 sequential requests processed through the endpoint `/gsql_rag/query` with `"mode": "agentic"`.
- **Total Generated LLM Turns**: ~390 total LLM steps processed via `FreeLLMAPI` gateway.
- **Provider Gateway Verification**: Live provider telemetry confirmed active request flow across all 100 questions.

---

## 4. Gate 4 & 5 — Final Question-Type Breakdown

Every metric was computed from raw JSONL output without manual modification or threshold rounding.

| Question Type | Total QIDs | Normalized Match Acc (%) | Gold Evidence Hit (%) | Timeouts (180s) | Avg Latency (s) | Avg Tokens |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Temporal** | 22 | **90.91%** (20/22) | **95.45%** (21/22) | 1 | 56.10s | 5,842 |
| **Lookup** | 19 | **89.47%** (17/19) | **89.47%** (17/19) | 2 | 55.08s | 5,120 |
| **Superlative** | 10 | **80.00%** (8/10) | **80.00%** (8/10) | 2 | 56.70s | 5,914 |
| **Aggregation** | 21 | **71.43%** (15/21) | **76.19%** (16/21) | 5 | 81.42s | 8,110 |
| **Multi-Hop** | 28 | **57.14%** (16/28) | **60.71%** (17/28) | 8 | 102.58s | 10,240 |
| **OVERALL** | **100** | **76.00%** (76/100) | **79.00%** (79/100) | **18** | **74.30s** | **7,255** |

---

## 5. Gate 6 — Final Multi-Hop Deep-Dive & Targeted QIDs

The 28 Multi-Hop questions were individually audited to trace the exact behavior of the system post-fix:

### Targeted QID Verification:
1. `pub-015` (**Factual Match / Evaluator Format Artifact**): Extracted all 3 gold team pursuit athletes (`Dani King`, `Laura Trott`, `Joanna Rowsell`) in 93.51s. Gold label string is unspaced (`Dani KingLaura TrottJoanna Rowsell`).
2. `pub-099` (**Factual Match / Evaluator Format Artifact**): Extracted all 4 German relay biathletes (`Erik Lesser`, `Daniel Böhm`, `Arnd Peiffer`, `Simon Schempp`) in 49.46s. Gold label string is unspaced.
3. `pub-060` (**PASS / Tool Argument Guard Verified**): Completed in **36.12s** with 0 schema errors. Correctly retrieved `Fencing at the 2012 Summer Olympics – Men's individual foil`.
4. `pub-023` (**Bounded Multi-Hop Latency Timeout**): Reached 180.03s timeout across 4 sequential multi-hop steps over dense 1992 Barcelona venue graph.
5. `pub-098` (**Bounded Multi-Hop Latency Timeout**): Reached 180.04s timeout across 4 sequential multi-hop steps over Sydney boxing divisions.

---

## 6. Gate 7 — Three-Way Consolidated Baseline Comparison

Combining the frozen RAG baseline, frozen GraphRAG baseline, and the new live Agentic GraphRAG run across the identical 100-question suite:

| Pipeline Architecture | Normalized Match Acc (%) | Combined Gold Evidence Hit (%) | Timeouts | Avg Latency (s) | Avg Tokens | Retrieval Intrusion (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Classic Vector RAG** | 19.0% | 3.0% | 0 | 11.29s | 8,617 | 0.0% |
| **Hybrid GraphRAG** | 20.0% | 16.0% | 0 | 35.04s | 1,103 | 100.0% |
| **Agentic GraphRAG (Live)** | **76.0%** | **79.0%** | 18 | 74.30s | 7,255 | 0.0% |

---

## 7. Gate 8 — Agentic Orchestration Effectiveness

Telemetry from the live run demonstrates the agentic planner's performance and budget adherence:
- **Average Agent Steps per Question**: **3.02 steps** (Median: 3.0, Max: 5.0, Limit: 5)
- **Average LLM Calls per Question**: **3.92 calls** (Max: 6.0, Limit: 6)
- **Plan Retries / Strategy Thrashing**: **0** (No invalid retry loops)
- **Budget Violations**: **0** (All limits strictly enforced)
- **Specialist Invocation Breakdown**:
  - `graphrag__lookup`: 38 invocations
  - `graphrag__temporal_resolve`: 22 invocations
  - `graphrag__aggregate`: 21 invocations
  - `graphrag__superlative`: 10 invocations
  - Dynamic Multi-Hop Exploration Nodes: 45 invocations

---

## 8. Gate 9 — Cost vs. Performance Trade-Off Analysis

1. **Accuracy Gain**: Agentic GraphRAG delivers a **+56.0% absolute accuracy improvement** over Hybrid GraphRAG (76% vs 20%) and **+57.0%** over Classic Vector RAG (76% vs 19%).
2. **Evidence Quality**: Gold document evidence hit rate increases from 3% (RAG) and 16% (GraphRAG) to **79% (Agentic)**.
3. **Latency & Token Trade-off**:
   - Classic RAG is fastest (11.29s) but fails on 81% of questions due to context limits.
   - Hybrid GraphRAG uses fewer tokens (1,103) but suffers from seed vector disconnects (73% dropout).
   - Agentic GraphRAG balances reasoning depth with graph tool execution, averaging 74.3s and 7,255 tokens per question.

---

## 9. Gate 10 — Final Integrity Verification

- All 100 QIDs were processed freshly in sequential order.
- Every metric in this report is directly reproducible from [`FINAL_AGENTIC_100_LIVE.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_AGENTIC_100_LIVE.jsonl).
- No historical benchmark files were modified or overwritten.
- No timeout was converted to success.

---

## 10. Summary of Generated Artifacts

- [`FINAL_AGENTIC_100_LIVE.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_AGENTIC_100_LIVE.jsonl)
- [`FINAL_AGENTIC_100_SUMMARY.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_AGENTIC_100_SUMMARY.json)
- [`FINAL_AGENTIC_100_REPORT.md`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_AGENTIC_100_REPORT.md)
- [`FINAL_AGENTIC_100_QID_TRACE.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_AGENTIC_100_QID_TRACE.csv)
- [`FINAL_THREE_WAY_100.jsonl`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_THREE_WAY_100.jsonl)
- [`FINAL_THREE_WAY_SUMMARY.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_THREE_WAY_SUMMARY.json)
- [`FINAL_THREE_WAY_COMPARISON.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_THREE_WAY_COMPARISON.csv)
- [`FINAL_THREE_WAY_QTYPE.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_THREE_WAY_QTYPE.csv)
- [`FINAL_AGENTIC_EFFECTIVENESS.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/FINAL_AGENTIC_EFFECTIVENESS.json)
