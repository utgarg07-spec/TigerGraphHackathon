# PHASE 14D-S — PRE-LIVE AGENTIC PIPELINE HARDENING

**Status**: `PASS — PRE-LIVE HARDENING COMPLETE`  
**Mode**: `IMPLEMENTATION + OFFLINE VALIDATION ONLY`  
**API Calls**: `0`  
**Live Questions Executed**: `0`  

---

## Executive Summary

Phase 14D-S conducted a exhaustive pre-live audit and hardening of all runtime contracts across the Agentic GraphRAG pipeline prior to authorizing live benchmark questions. No external LLM API calls, benchmark question executions, or model downloads were performed. Every contract gate (Gate 0 through Gate 12) was statically audited and validated via offline mock test suites.

---

## 1. Source-Grounded Pipeline Contract Map

```
Question Input
  │
  ▼
AIRouter Integration (base_url=https://api.airouter.in/v1, ChatOpenAI max_retries=0)
  │
  ▼
base_llm.py Retry Owner (MAX_PROVIDER_ATTEMPTS=2, circuit breaks on 402/quota)
  │
  ▼
agentic_planner.py (Plan generation with PydanticOutputParser & _repair_olympic_args)
  │
  ├──► [Planner failure / parse error] ──► Bounded Keyword Fallback Plan
  │
  ▼
agentic_graph.py (Orchestrator: MAX_REPLANS=1, MAX_TOTAL_STEPS=20)
  │
  ▼
Deterministic Tool Execution (lookup, aggregate, superlative, temporal, hybrid_search)
  │
  ▼
tigergraph_embedding_store.py (retrieve_similar_with_score)
  │
  ├──► 1024-d query vector ──► GraphRAG_Hybrid_Qwen_Vector_Search.gsql ──► v.qwen_embedding (1024-d)
  │
  ├──► GSQL error ──────────► Explicit RuntimeError raised (Observability preserved)
  │
  ▼
agentic_synthesizer.py (_gather context -> TigerGraphAgentGenerator)
  │
  ▼
unified_evaluator.py (Current Phase 14D-K evaluator mounted via ./benchmark/:/code/benchmark)
```

---

## 2. Gate-by-Gate Contract Audit Results

### Gate 1 — AIRouter Contract Audit
- **Endpoint**: `https://api.airouter.in/v1` via `ChatOpenAI`.
- **API Key**: Read exclusively from `AIROUTER_API_KEY` environment variable.
- **Model**: `openai/gpt-oss-20b` (configurable).
- **Timeouts**: Bounded at 180s in `httpx.Client` (`connect=60.0`, `read=180.0`, `write=60.0`).
- **Retry Invariants**: `ChatOpenAI max_retries = 0`. `base_llm.py` is sole retry owner with `MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL = 2`.
- **Quota/402 Handling**: 402 and daily quota errors trip `_circuit_broken_providers` immediately with 0 retries.

### Gate 2 — Structured Output Contract
- **Parsing Hierarchy**: `PydanticOutputParser` -> regex repair -> `_repair_olympic_args` -> bounded keyword fallback.
- **Argument Repairs**: `_repair_olympic_args` extracts supported games (`2018 Winter Olympics`), sports (`biathlon`), event names, and thresholds without inventing random arguments.
- **Parser Failure**: Parser exceptions catch safely and produce a valid fallback `Plan` without crashing or triggering LLM retries.

### Gate 3 — Planner Contract
- **Prompt Isolation**: `SystemMessage` and `HumanMessage` objects isolate prompts, preventing string formatting syntax errors from literal `{}` braces.
- **Budget Protection**: `BudgetExceededError` terminates planning cleanly without infinite loops.
- **Sanitization**: `_sanitize` validates tool names against `registry.catalog` and enforces required question arguments.

### Gate 4 — Agentic Graph / Replan Contract
- **Replan Cap**: `MAX_REPLANS = 1` strictly enforced.
- **Loop Termination**: The replan loop breaks (`break`) if `has_context(results)` is `True` OR `replans >= MAX_REPLANS`.
- **Infrastructure Error Visibility**: GSQL failures raise `RuntimeError` and remain visible in `agent_steps` telemetry.

### Gate 5 — Qwen / TigerGraph Vector Query Contract
- **Routing**: 1024-d query vectors route exclusively to `GraphRAG_Hybrid_Qwen_Vector_Search`.
- **Target Field**: Operates on `v.qwen_embedding` (1024-d).
- **Legacy Path Isolation**: The legacy 1536-d query `get_topk_similar` operates on `v.embedding` (1536-d) and is NEVER called for 1024-d query vectors.

### Gate 6 & 7 — Evidence -> Synthesis Contract & Hardening
- **Context Propagation**: `_gather` collects all retrieved step contexts into structured and unstructured buckets.
- **Synthesis Grounding**: Contexts are passed to `TigerGraphAgentGenerator.generate_answer`.
- **No-Answer State**: If context is missing or synthesis fails, returns a controlled `answered_question=False` response.

### Gate 8 — Live-Smoke Runner Audit
- **Evaluator Path**: Imports `unified_evaluator.py` dynamically from `/code/benchmark`.
- **Telemetry**: Records `logical_llm_calls`, `provider_http_attempts`, `retries`, `failovers`, `agent_steps`, `tool_calls`, `latency_s`, and `evaluator_score`.

### Gate 9 — Docker Source Consistency
- **Volume Mount**: `./benchmark/:/code/benchmark` mounted in `docker-compose.yml` under `graphrag` service.
- **Evaluator Parity**: Ensures container evaluator code matches host repository evaluator exactly.

---

## 3. Static Invariants Verification

| Invariant | Value | Status |
| :--- | :--- | :--- |
| `MAX_LLM_CALLS_PER_QUESTION` | `6` | VERIFIED |
| `MAX_PLAN_RETRIES` | `2` | VERIFIED |
| `MAX_REPLANS` | `1` | VERIFIED |
| `MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL` | `2` | VERIFIED |
| `ChatOpenAI max_retries` | `0` | VERIFIED |
| Active Qwen Vector Query | `GraphRAG_Hybrid_Qwen_Vector_Search` | VERIFIED |
| Active Vector Field | `v.qwen_embedding` (1024-d) | VERIFIED |
| Legacy Vector Field | `v.embedding` (1536-d, untouched) | VERIFIED |
| Docker Evaluator Volume | `./benchmark/:/code/benchmark` | VERIFIED |

---

## 4. Offline Test Suite Execution Results

1. **`py_compile` Checks**: `PASS`
   - `scratch/test_phase14d_s_prelive_hardening.py`
   - `scratch/test_phase14d_r_contracts.py`

2. **Phase 14D-R Contract Test Suite**: `5/5 PASS`
   - [`scratch/test_phase14d_r_contracts.py`](file:///d:/Hackathons/TigerGraph/scratch/test_phase14d_r_contracts.py)

3. **Evaluator Normalization Test Suite**: `16/16 PASS`
   - [`scratch/test_evaluator_number_word_normalization.py`](file:///d:/Hackathons/TigerGraph/scratch/test_evaluator_number_word_normalization.py)

4. **Phase 14D-S Pre-Live Hardening Test Suite**: `7/7 PASS`
   - [`scratch/test_phase14d_s_prelive_hardening.py`](file:///d:/Hackathons/TigerGraph/scratch/test_phase14d_s_prelive_hardening.py)

**Total Offline Tests Executed**: `28/28 PASS (100%)`

---

## Final Status

`PASS — PRE-LIVE HARDENING COMPLETE`
