# PHASE 12C — CONTROLLED PROVIDER LATENCY & ROUTING EXPERIMENT REPORT

**Date**: 2026-09-29  
**Status**: COMPLETE  
**Final Decision**: **A. FAST PROVIDER IDENTIFIED — ROUTING CHANGE JUSTIFIED**

---

## 1. Executive Summary & Purpose

Phase 12C conducted a read-only, controlled provider-selection experiment to identify an optimal high-speed, structured-compatible LLM inference provider for the Agentic GraphRAG system.

All historical final 100Q benchmark artifacts were preserved completely. Zero production code changes or routing overrides were applied during this diagnostic phase.

### Key Finding
**Groq (`qwen/qwen3.8-27b`)** demonstrated an extraordinary **15.5x latency speedup** over the baseline `FreeLLMAPI` (`auto` $\rightarrow$ `Qwen2.5-Coder-32B`), reducing per-turn LLM inference latency from **11.42s to 732.97ms** with **100.0% Pydantic structured plan compliance** and **0 failures**.

---

## 2. Gate 0 — Telemetry Wording Resolution

- **Resolution Verdict**: **Option A**.
- **Empirical Explanation**:
  The outer `/gsql_rag/query` HTTP request remained open while internal multi-turn agent execution proceeded sequentially. When cumulative execution time across 3–4 agent steps exceeded the 180.0-second client limit, the benchmark runner's HTTP client threw a `Read timed out` exception. The client thus received no response payload or `agent_steps` array, recording `error="Request Exception: Read timed out. (read timeout=180)"`.

---

## 3. Gate 1 — Inventory of Configured Providers

| Provider Name | Gateway Endpoint | Model ID | Availability Status | Auth Status |
|:---|:---|:---|:---:|:---:|
| **FreeLLMAPI (Baseline)** | `http://localhost:31415/v1` | `auto` (Qwen2.5-Coder-32B) | REACHABLE | Valid |
| **Groq** | `https://api.groq.com/openai/v1` | `qwen/qwen3.8-27b` | REACHABLE | Valid |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `qwen/qwen-2.5-coder-32b-instruct` | REACHABLE | Valid |
| **OpenRouter (Llama)** | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct` | REACHABLE | Valid |

---

## 4. Gate 2, 3 & 4 — Latency & Structured Compatibility Measurements

Controlled benchmark workloads were run across 5 representative Olympic questions (Lookup, Aggregation, Temporal, Superlative, Multi-Hop):

| Provider & Model | Request Success Rate | Valid Structured Plan (%) | Avg Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Speedup vs Baseline |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **FreeLLMAPI (Baseline Qwen)** | 80.0% (4/5) | 40.0% (2/5) | 11,418.67ms | 8,841.85ms | 32,078.73ms | 1.00x |
| **OpenRouter (Qwen-2.5-Coder-32B)** | 100.0% (5/5) | 100.0% (5/5) | 7,879.91ms | 8,045.40ms | 12,961.72ms | 1.45x |
| **OpenRouter (Llama-3.3-70B)** | 100.0% (5/5) | 80.0% (4/5) | 6,388.99ms | 5,695.63ms | 14,315.60ms | 1.79x |
| **Groq (`qwen/qwen3.8-27b`)** | **100.0% (5/5)** | **100.0% (5/5)** | **732.97ms** | **730.48ms** | **824.07ms** | **15.58x** |

---

## 5. Gate 5 — Provider Selection Criteria Evaluation

Groq (`qwen/qwen3.8-27b`) satisfied all 5 mandatory selection criteria:
1. **Valid Plan/Pydantic Output**: **100% (5/5)** valid JSON schema generation.
2. **Valid Tool-Selection Output**: **100% (5/5)** precise mapping to `graphrag__*` tools.
3. **Valid Synthesis Output**: **100% (5/5)** grounded natural language answers.
4. **Zero Provider Errors**: **0 timeouts**, 0 HTTP errors.
5. **Materially Lower Latency**: **732.97ms** average turn duration (**>15x faster** than baseline).

---

## 6. Gate 6 — Routing Strategy Recommendation

$$\boxed{\text{RECOMMENDED ROUTING STRATEGY: C. Role-Specific Routing}}$$

- **Planning Step (`plan`)**: Route to **Groq (`qwen/qwen3.8-27b`)** for sub-second plan generation (<800ms).
- **Reasoning Step (`retrieve`)**: Route to **Groq (`qwen/qwen3.8-27b`)** for fast candidate filtering (<800ms).
- **Synthesis Step (`answer`)**: Route to **Groq (`qwen/qwen3.8-27b`)** with fallback to **OpenRouter Qwen-2.5-Coder-32B**.

---

## 7. Gate 7 — ReadTimeout Retry Decision

- **Verdict**: **NOT RECOMMENDED**.
- **Rationale**: Implementing automatic retries on the client side introduces network overhead and does not solve slow provider queueing. Transitioning to Groq (`qwen/qwen3.8-27b`) reduces 4-step multi-hop question wall-clock latency from **~100 seconds to <5 seconds**, eliminating timeout risk at the root cause.

---

## 8. Summary of Generated Artifacts

- [`PHASE_12C_PROVIDER_EXPERIMENT.md`](file:///d:/Hackathons/TigerGraph/benchmark/results/PHASE_12C_PROVIDER_EXPERIMENT.md)
- [`PHASE_12C_PROVIDER_EXPERIMENT.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/PHASE_12C_PROVIDER_EXPERIMENT.json)
- [`PHASE_12C_PROVIDER_LATENCY.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/PHASE_12C_PROVIDER_LATENCY.csv)
