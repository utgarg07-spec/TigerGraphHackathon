# PHASE 13 — GATE 1: PROVIDER ROUTING IMPLEMENTATION PLAN

**Date**: 2026-09-29  
**Status**: PASS — READ-ONLY PLAN COMPLETE  

---

## 1. Objective & Target Architecture

Implement the production provider routing improvement identified by the Phase 12B/12C diagnostic audits:

```
planning   -> Groq / qwen/qwen3.8-27b
reasoning  -> Groq / qwen/qwen3.8-27b
synthesis  -> Groq / qwen/qwen3.8-27b
synthesis fallback -> OpenRouter / qwen/qwen-2.5-coder-32b-instruct
```

Existing FreeLLMAPI support will remain available and un-deleted. No hardcoded API keys or secrets will be introduced.

---

## 2. Exact Files Proposed for Modification

1. `common/llm_services/groq_llm_service.py`:
   - Update secondary fallback provider to use OpenRouter with `qwen/qwen-2.5-coder-32b-instruct`.
   - Ensure `ChatGroq` handles model kwargs and structure invocation cleanly.
2. `configs/local_server_config.json` & `configs/server_config.json`:
   - Update `completion_service` to set `"llm_service": "groq"` and `"llm_model": "qwen/qwen3.8-27b"`.
   - Preserve all existing API keys in `authentication_configuration`.

---

## 3. Configuration & Fallback Behavior

- **Primary Provider**: Groq API (`ChatGroq`) using model `qwen/qwen3.8-27b`.
- **Fallback Provider**: OpenRouter (`ChatOpenAI` at `https://openrouter.ai/api/v1`) using model `qwen/qwen-2.5-coder-32b-instruct`.
- **Fallback Trigger**: Handled automatically by `_execute_with_fallback` in `common/llm_services/base_llm.py` on transient provider errors (HTTP 429, 502, 503, 402/rate-limit).
- **Agent Execution Budgets**:
  - `MAX_AGENT_STEPS = 5` (Unchanged)
  - `MAX_LLM_CALLS_PER_QUESTION = 6` (Unchanged)
  - `MAX_PLAN_RETRIES = 2` (Unchanged)

---

## 4. Verification & Testing Requirements

1. **Gate 2**: Apply minimal routing change and verify `git diff --check`.
2. **Gate 3**: Provider contract & structured output test across 5 calls (Pydantic plan, tool selection, reasoning, synthesis). Target: $\ge 5/5$ PASS.
3. **Gate 4**: Telemetry observability verification ensuring step logs record `provider: groq` and fallback behavior when triggered.
4. **Gate 5**: Phase 6 regression suite (**78/78 PASS**) + 9 targeted regression questions (`pub-004`, `pub-008`, `pub-015`, `pub-023`, `pub-060`, `pub-067`, `pub-076`, `pub-098`, `pub-099`).
5. **Gate 6**: 5-question end-to-end agentic smoke test (0 timeouts, 5/5 HTTP success).
6. **Gate 7**: 25-question post-fix performance benchmark.
