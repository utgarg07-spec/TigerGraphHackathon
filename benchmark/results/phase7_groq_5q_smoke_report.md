# Phase 7 — Groq Agentic Pipeline Stabilization & 5-Question Smoke Test Report

**Target Model**: `openai/gpt-oss-20b`  
**Provider**: Groq API  
**Target Mode**: `mode=agentic` | `agent_style=planned` | `pass_qtype=False`  
**Configuration**: `reasoning_effort=low` | `temperature=0`  
**Execution Safety Ceiling**: `MAX_LLM_CALLS_PER_QUESTION=6` | `MAX_PLAN_RETRIES=2` | `MAX_AGENT_STEPS=5`

---

## 1. Inspection Findings & Architecture Summary

### Baseline Findings & Call Flow
1. **LLM API Invocations**: Performed via `llm.invoke_structured` for planning/triage, `llm.bind_tools` for agent step execution, and `llm.invoke` for answer synthesis.
2. **Plan Generation**: Occurs inside `plan_question` (`graphrag/app/agent/agentic_planner.py`).
3. **Plan / Schema Recovery**: Structured output adapter `_try_recover_structured` in `common/llm_services/base_llm.py` extracts raw JSON arguments when Groq function-call validation fails.
4. **Retry Loop Unboundedness Audit**: Previously, replanning was capped locally, but no global hard budget tracked LLM calls across structured parsing, retries, 429 rate-limit backoffs, and agent steps.
5. **HTTP 429 Handling**: Upgraded to inspect `exc.response.headers` (`retry-after`, `x-ratelimit-remaining-requests`, `x-ratelimit-remaining-tokens`) and enforce budget-counted retries.

### Files Modified & Rationale
- `common/llm_services/groq_llm_service.py`: Added explicit `reasoning_effort="low"` support to `ChatGroq`.
- `configs/local_server_config.json`: Updated completion configuration to `llm_service="groq"`, `llm_model="openai/gpt-oss-20b"`, and `reasoning_effort="low"`.
- `common/llm_services/base_llm.py`: Added `QuestionBudgetTracker` (ContextVar) and `BudgetExceededError` enforcing hard limits (`MAX_LLM_CALLS_PER_QUESTION=6`, `MAX_PLAN_RETRIES=2`, `MAX_AGENT_STEPS=5`), HTTP 429 rate-limit header parsing, and budget accounting.
- `graphrag/app/agent/agentic_planner.py`: Re-raises `BudgetExceededError` immediately on budget exhaustion.
- `graphrag/app/agent/agentic_executor.py`: Calls `tracker.record_agent_step` in `_run_step` to enforce `MAX_AGENT_STEPS=5`.
- `graphrag/app/agent/agentic_graph.py`: Wraps orchestrator in `start_question_budget`, catches `BudgetExceededError`, records per-question metrics into `query_sources`, and cleans up via `finally`.
- `scratch/run_5q_smoke.py`: Created 5-question HTTP benchmark runner script.

### Intentionally Untouched Files (Phase 1–6 Protection)
- `graphrag/app/tools/olympic_tools.py` (Deterministic Phase 6 tools: 78/78 tests pass)
- `graphrag/app/tools/tool_registry.py` (Phase 6 tool registry)
- `common/gsql/supportai/retrievers/*` (GSQL queries & schema)
- `common/embeddings/*` (Qwen embeddings & vector store)
- `data/eval_public.jsonl` (Public benchmark dataset)

---

## 2. Exactly 5 Benchmark Questions Execution Trace

| QID | Question Type | Success / Fail | Elapsed (s) | LLM Calls | Plan Retries | Agent Steps | Deterministic Tool Calls | Exact Tool Names | Hybrid Fallbacks | HTTP 429 Count | Input Tokens | Output Tokens | Failure Reason |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **pub-009** | Lookup | **Success** | 15.85s | 3 | 1 | 1 | 0 | `graphrag__hybrid_search` | 1 | 0 | 4,525 | 89 | None |
| **pub-002** | Temporal | **Success** | 30.22s | 2 | 0 | 1 | 1 | `graphrag__temporal_resolve` | 0 | 0 | 3,053 | 295 | None |
| **pub-001** | Aggregation | **Success** | 80.59s | 3 | 1 | 1 | 0 | `graphrag__hybrid_search` | 1 | 0 | 5,430 | 132 | None |
| **pub-004** | Superlative | **Success** | 80.04s | 3 | 1 | 1 | 0 | `graphrag__hybrid_search` | 1 | 0 | 5,540 | 226 | None |
| **pub-005** | Multi-hop | **Success** | 82.43s | 4 | 1 | 1 | 0 | `graphrag__hybrid_search` | 1 | 1 | UNAVAILABLE | UNAVAILABLE | None |

---

## 3. Cumulative Execution & Metric Summary

- **Total Questions**: 5
- **Successful Questions**: 5 (100%)
- **Failed Questions**: 0 (0%)
- **Total LLM Calls**: 15 (Average: 3.0 calls/question, max ceiling: 6)
- **Total Agent Steps**: 5 (Average: 1.0 step/question, max ceiling: 5)
- **Total Plan Retries**: 4 (Average: 0.8 retries/question, max ceiling: 2 per question)
- **Total Deterministic Tool Calls**: 1 (`graphrag__temporal_resolve`)
- **Tool Call Breakdown**:
  - `graphrag__hybrid_search`: 4
  - `graphrag__temporal_resolve`: 1
- **Total Hybrid Fallbacks**: 4
- **Total HTTP 429 Rate-Limits Encountered**: 1 (Captured, parsed retry-after header, retried cleanly within call budget)
- **Rate-Limit Information Captured**: `retry-after` header parsed, remaining request/token counters extracted
- **Total Input Tokens**: 18,548 (across questions reporting tokens)
- **Total Output Tokens**: 742 (across questions reporting tokens)
- **Average Latency**: 57.82s
- **Maximum Latency**: 82.43s (pub-005)
- **Budget-Exhausted Questions**: 0
- **Unbounded Retry Occurred**: **FALSE** (Zero infinite loops or unconstrained retry paths)
- **5-Question Execution Safety Gate**: **PASSED**

---

## 4. Assessment & Recommendation

- **Execution Safety Gate Status**: **PASSED**. The hard budgets (`MAX_LLM_CALLS_PER_QUESTION=6`, `MAX_PLAN_RETRIES=2`, `MAX_AGENT_STEPS=5`) successfully bounded every request lifecycle, and HTTP 429 handling operated strictly within the LLM call budget.
- **Ready for 100-Question Benchmark**: **READY FOR 100Q BENCHMARK** (Pending explicit user instruction, as instructed by the user prompt to stop after 5 questions).
