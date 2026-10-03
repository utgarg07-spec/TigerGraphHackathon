# PHASE 14D-H — RETRY ARCHITECTURE AUDIT REPORT

## 1. Retry Ownership & Architecture Specification
- **Single Retry Owner**: `base_llm._execute_with_fallback()` owns provider failover, transient retry policy, and rate-limit backoff.
- **Provider Client Configuration**: `ChatOpenAI` in `airouter_llm_service.py` is configured with `max_retries = 0`. Provider SDKs DO NOT perform application-level retries.
- **Transport Timeouts**: `httpx.Client` uses `timeout=180.0` (`connect=60.0s`, `read=180.0s`). Transport is purely a socket timeout enforcement layer, not an application retry layer.

## 2. Invariants & Policy Bounds
1. **MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL = 2**: For any single logical LLM call, a candidate provider receives at most 1 initial attempt + 1 retry attempt (maximum 2 HTTP requests total).
2. **HTTP 402 / Credit Exhaustion**: Retries = 0. Immediate circuit break & failover.
3. **Daily Quota / Permanent 429**: Retries = 0. Immediate circuit break & failover.
4. **Transient 429 (Retry-After <= 30s)**: Max 1 retry after bounded wait ($X + 0.5s$).
5. **HTTP 5xx / Connection Errors / Timeouts**: Max 1 retry attempt.
6. **Parser Failure**: Operates on response already received; does NOT issue another provider HTTP request for parsing failures.
7. **QuestionBudgetTracker**: `logical_llm_calls` (budget cap = 6) reserved BEFORE provider HTTP requests occur. Provider retries do NOT consume additional logical call slots.
8. **MAX_REPLANS = 1**: Maximum 1 recovery replan cycle after initial plan. Successful retrievals (`has_context == True`) immediately exit loop without replanning.

## 3. Static Invariants Verification Matrix

| Invariant | Status | Verification Evidence |
|---|---|---|
| INVARIANT 1: ChatOpenAI max_retries == 0 | **PASS** | `airouter_llm_service.py` line 57 |
| INVARIANT 2: httpx no retry policy | **PASS** | `airouter_llm_service.py` lines 38-45 |
| INVARIANT 3: Provider attempts <= 2 | **PASS** | `base_llm.py` `MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL = 2` |
| INVARIANT 4: No HTTP 402 retried | **PASS** | `base_llm.py` `is_hard_credit` circuit break |
| INVARIANT 5: No permanent quota retried | **PASS** | `base_llm.py` `is_hard_quota` circuit break |
| INVARIANT 6: Transient retry <= 1 | **PASS** | `base_llm.py` `provider_retries` cap |
| INVARIANT 7: Budget counts logical calls | **PASS** | `base_llm.py` `record_llm_call()` |
| INVARIANT 8: Provider retries separately tracked | **PASS** | `base_llm.py` telemetry `http_attempts`, `retries`, `failovers` |
| INVARIANT 9: Budget cap 6 enforced | **PASS** | `base_llm.py` `BudgetExceededError` |
| INVARIANT 10: MAX_REPLANS == 1 | **PASS** | `agentic_graph.py` line 35 |
| INVARIANT 11: Sufficient context stops replan | **PASS** | `agentic_graph.py` line 119 (`has_context(results)`) |
| INVARIANT 12: 2nd insufficient result stops replan | **PASS** | `agentic_graph.py` line 119 (`replans >= max_replans`) |
| INVARIANT 13: Non-recursive fallback | **PASS** | `agentic_planner.py` keyword-based fallback using `_repair_olympic_args` |
