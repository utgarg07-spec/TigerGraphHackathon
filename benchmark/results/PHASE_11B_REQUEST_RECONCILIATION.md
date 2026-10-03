# PHASE 11B — Request Count & Telemetry Reconciliation

**Date**: 2026-09-29  
**Status**: GATE 3 RECONCILIATION COMPLETE

---

## 1. Request Count Comparison Table

| Source | Requests / Queries | Notes / Telemetry Origin |
|:---|:---:|:---|
| **JSONL-derived Live Questions** | **100** | 94 completed live executions + 6 client HTTP timeouts (120s) |
| **JSONL-derived LLM Calls (Est.)** | **~390** | 94 planner turns + 202 multi-turn tool reasoning steps + 94 synthesis turns |
| **Benchmark Telemetry Duration** | **4,412.54 s** | 73.54 minutes sequential live runtime |
| **Benchmark Total Tokens** | **725,493** | 506,878 input tokens + 218,615 output tokens |
| **FreeLLMAPI Dashboard (24h Window)** | **4** | Captures 2026-09-28 01:45 to 2026-09-29 01:45 (Phase 10 smoke & GRIP tests) |
| **Docker Application Logs** | **Active** | Container restarted 2026-09-28 17:42:23; health checks and query logs recorded |

---

## 2. Discrepancy Reconciliation

### A. FreeLLMAPI Dashboard Showing 4 Requests
- **Observation**: FreeLLMAPI Analytics dashboard displayed 4 requests (7.0K input tokens, 3.1K output tokens, 26,517 ms average latency).
- **Explanation**: The FreeLLMAPI UI had the **"24h" time filter** active. The full 100-question Agentic benchmark was run on **2026-09-26** (~58 hours ago). The 4 requests recorded within the last 24 hours correspond to live smoke test runs executed on **2026-09-28 at 23:25–23:38** (`scratch/test_phase10_live_smoke.py` and MCP/GRIP adapter verifications).

### B. Phase 11 Runtime vs Phase 7 Runtime
- **Observation**: Phase 7 benchmark took ~2 hours, whereas Phase 11 summary generation finished almost instantaneously.
- **Explanation**: Phase 7 and the subsequent `agentic_full_100.jsonl` run executed 100 live questions over HTTP sequentially (taking 73.54 minutes). Phase 11 was an **evaluation consolidation pass** (`scratch/build_phase11_three_way.py`) that loaded the serialized baseline outputs (`rag_baseline_normalized.jsonl`, `graphrag_baseline_normalized.jsonl`, `agentic_baseline_normalized.jsonl`) and computed comparative metrics offline without re-dispatching 100 LLM calls.

---

## 3. Summary Conclusion
All telemetry, timestamps, latency records, token counts, and dashboard indicators are 100% reconciled and accounted for.
