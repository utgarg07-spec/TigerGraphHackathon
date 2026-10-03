# PHASE 14 — GATE 5 STALL INVESTIGATION & AUDIT REPORT

**Date**: 2026-09-30  
**Target Repo**: `D:\Hackathons\TigerGraph`  
**Investigation Mode**: READ-ONLY AUDIT  
**Status**: COMPLETE  

---

## 1. Executive Summary

During Phase 14 Gate 5 (25-Question Sanity Benchmark on `pub-026` – `pub-050`), execution experienced elevated latency (~117.73s/question, total ~49 minutes per 25Q pass) and spanned ~2.5 hours due to multiple overlapping container processes.

### Key Audit Findings:
1. **Ollama Traffic is 100% Embeddings (Option A)**:
   - Port `11434` (`host.docker.internal:11434`) was used exclusively for `qwen3-embedding:0.6b` vector similarity embedding generation via `embedding_services.py: embed_query()`.
   - **Zero generative LLM calls** were routed to Ollama. This is expected and is **NOT** a provider-routing regression.
2. **Groq Daily Token Quota (TPD) Exhaustion**:
   - Groq API returned `HTTP 429 Too Many Requests` (`Rate limit reached for model qwen/qwen3.8-27b ... tokens per day Limit: 200,000, Used: ~199,800`).
3. **OpenRouter LangChain Parameter Bug (402 Payment Required)**:
   - When failing over from Groq to OpenRouter `qwen/qwen-2.5-coder-32b-instruct`, `langchain_openai.ChatOpenAI` converted `max_tokens=512` into `max_completion_tokens: 512`.
   - OpenRouter ignored `max_completion_tokens` on non-o1 models and assumed a default context window reservation of up to 28,935 tokens against an account balance limit of ~20,500 tokens, returning `HTTP 402 Payment Required`.
4. **FreeLLMAPI Connection Timeouts**:
   - The tertiary fallback to FreeLLMAPI suffered repeated connection drops (`openai.APIConnectionError: Connection error` / `SSL UNEXPECTED_EOF_WHILE_READING`) taking 60–90 seconds of retries per turn before timing out and returning graceful agent generation failure strings.
5. **Multiple Overlapping Container Processes**:
   - Killing the Windows host PowerShell wrappers did not send SIGTERM to `docker exec` processes inside the Linux container, leaving background worker PIDs (916, 975, 1046, 1228, 1365) running concurrently.

---

## 2. Gate-by-Gate Diagnostic Analysis

### Gate A — Runner Inspection (`scratch/run_gate5_25q_sanity_p14.py`)
- **Direct Invocation**: Invokes `agent.question_for_agent(qtext)` directly in-process via `make_agent("Olympics", conn, mode="agentic")`.
- **Factory**: Uses the production provider factory `get_llm_service(get_chat_config("Olympics"))`.
- **Provider Roles**:
  - Planning: `Groq` (`qwen/qwen3.8-27b`)
  - Reasoning: `Groq` (`qwen/qwen3.8-27b`)
  - Synthesis: `Groq` (`qwen/qwen3.8-27b`)
  - Fallback 1: `OpenRouter` (`qwen/qwen-2.5-coder-32b-instruct`)
  - Fallback 2: `FreeLLMAPI` (`openai/auto`)
  - Embeddings: `Ollama` (`qwen3-embedding:0.6b`)

### Gate B — Distinguish Generation from Embedding Traffic
- Sockets connected to `192.168.65.254:11434` / `127.0.0.1:11434` correspond exclusively to `host.docker.internal:11434`.
- **Caller**: `embedding_services.py: embed_query()` via `TigerGraphEmbeddingStore`.
- **Model**: `qwen3-embedding:0.6b` (1536 / 1024 dimensional embeddings).
- **Verdict**: Generation was **NOT** routed to Ollama. Ollama traffic is embedding-only (**Option A**).

### Gate C — Provider Routing Trace
- **Production Contract Alignment**: Exact match with Phase 13 specification (`Groq` primary, `OpenRouter` secondary, `FreeLLMAPI` tertiary).

### Gate D — FreeLLMAPI Trace
- **FreeLLMAPI Traffic Attribution**: FreeLLMAPI received connection attempts during Gate 5 only after Groq (429) and OpenRouter (402) failed sequentially. Because FreeLLMAPI encountered connection errors and SSL resets, it did not successfully complete generation turns.

### Gate E — Latency & Time Allocation Breakdown
- Each of the 25 questions (`pub-026` to `pub-050`) experienced:
  1. Groq attempt -> immediate 429 (~0.1s)
  2. OpenRouter attempt -> immediate 402 (~0.1s)
  3. FreeLLMAPI attempt -> multiple HTTP retries with SSL reset / timeouts (~60s to ~120s)
  4. Salvage fallback generation output: `"I wasn't able to generate an answer for this question..."`
- Total runtime for 25 questions = 2,943.25 seconds (~49.05 minutes).
- Overlapping executions accumulated ~2.5 hours total runtime across container PIDs.

### Gate F — Phase 13 vs Phase 14 Comparison
| Dimension | Phase 13 Gate 7 | Phase 14 Gate 5 |
|---|---|---|
| Question Range | `pub-001` – `pub-025` | `pub-026` – `pub-050` |
| Groq Daily Token Limit Status | Under Quota (<150k TPD) | Exhausted (200k TPD reached) |
| Primary Provider Response | HTTP 200 OK (~0.3s) | HTTP 429 Rate Limit |
| OpenRouter Fallback Triggered | No | Yes (hit `max_completion_tokens` bug) |
| FreeLLMAPI Fallback Triggered | No | Yes (hit SSL/connection timeouts) |
| Normalized Accuracy | 48.0% (12/25) | 0.0% (0/25 due to cascade failure) |
| Mean Latency | 65.92s | 117.73s |

### Gate G — Safety & Rerun Classification
- **Classification**: `NEEDS_RUNNER_FIX` / `NEEDS_CONFIG_FIX`
- **Root Cause Fixes Identified**:
  1. Pass `extra_body={"max_tokens": max_tokens}` to `ChatOpenAI` fallback instances in `groq_llm_service.py` to prevent OpenRouter 402 credit reservation errors.
  2. Include connection errors/timeouts in `is_provider_err` inside `_execute_with_fallback` in `base_llm.py`.
  3. Clean up stale container worker processes (`kill -9`) before launching new benchmark runs.

---

## 3. Explicit Answers to the 12 Audit Questions

1. **Why did Gate 5 run for >2.5 hours?**  
   Each question took ~118s because every LLM turn traversed the entire 3-tier fallback chain (Groq 429 -> OpenRouter 402 -> FreeLLMAPI socket timeout/retries taking 60–120s). A single pass took ~49 minutes, and multiple orphaned runs launched in Docker over 2.5 hours.

2. **Did it actually make LLM generation calls?**  
   Yes. It made ~97 LLM generation attempts across triage, planning, and answer generation.

3. **Which provider handled those calls?**  
   Calls were dispatched to **Groq** (primary), fell back to **OpenRouter** (secondary), and finally attempted **FreeLLMAPI** (tertiary).

4. **Which model handled those calls?**  
   `qwen/qwen3.8-27b` on Groq, `qwen/qwen-2.5-coder-32b-instruct` on OpenRouter, and `openai/auto` on FreeLLMAPI.

5. **Were Ollama connections embedding-only or generation-related?**  
   **Embedding-only**. Every request to `127.0.0.1:11434` was for `qwen3-embedding:0.6b` vector query embedding generation.

6. **Did FreeLLMAPI receive traffic from this run?**  
   Yes. It received fallback connection requests after Groq and OpenRouter failed.

7. **Did Groq receive traffic from this run?**  
   Yes. Every question initially hit Groq and was rejected with HTTP 429 due to 200k daily token limit exhaustion.

8. **Which question/step was last active?**  
   `pub-050` (all 25 questions from `pub-026` to `pub-050` completed their turns and wrote final JSONL/JSON artifacts).

9. **Was there an unbounded wait/retry/loop?**  
   No infinite loop occurred; however, FreeLLMAPI's default retry backoff (~60–90s) caused bounded latency inflation on every turn.

10. **Is the Gate 5 runner safe to rerun?**  
    **No, not until the OpenRouter fallback parameter fix is confirmed and stale container processes are cleared.**

11. **What exact minimal fix, if any, is required?**  
    Explicitly supply `extra_body={"max_tokens": max_tokens}` to fallback `ChatOpenAI` instances in `groq_llm_service.py` so OpenRouter enforces a 512 token limit rather than reserving 28,000+ context window tokens.

12. **What should be tested before rerunning Gate 5?**  
    Run a direct 1-question smoke test (`agent.question_for_agent`) confirming that Groq (or OpenRouter fallback) returns HTTP 200 OK and generates a factual answer within <15 seconds.
