# FROZEN PRODUCTION STATE RECORD

**Timestamp:** 2026-10-02T02:10:00+05:30  
**Commit Hash:** `3fff41fbc04c89f0065e1bb2e68c3ba631784082`  
**Branch:** `main`

---

## 1. Frozen Production Configuration

### LLM Service (AIRouter)
- **Service:** `airouter`
- **Model:** `openai/gpt-oss-20b`
- **Base URL:** `https://api.airouter.in/v1`
- **Temperature:** `0`
- **Reasoning Effort:** `low`
- **Prompt Path:** `./common/prompts/openai_gpt4/`
- **Structured Output Handling:** Pydantic parser bypass active in `invoke_structured` and `invoke_with_parser` (Line 863 repair verified).

### Embedding Service
- **Service:** `ollama`
- **Model:** `qwen3-embedding:0.6b`
- **Output Dimensionality:** `1024`
- **Base URL:** `http://host.docker.internal:11434`
- **GSQL Hybrid Query:** `GraphRAG_Hybrid_Qwen_Vector_Search` (1024 dimensions)

### Database Configuration
- **Host:** `https://tg-eb6a2e24-db15-4708-b294-710c9f6af79b.tg-2635877100.i.tgcloud.io`
- **Graph Name:** `Olympics`
- **Default Timeout:** 300s

### Agent & Execution Invariants
- `MAX_LLM_CALLS_PER_QUESTION` = 6
- `MAX_PLAN_RETRIES` = 2
- `MAX_REPLANS` = 1
- `MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL` = 2
- `ChatOpenAI(max_retries=0)` (Retry ownership strictly in LLM_Model fallback executor)
- String type protection in `agentic_executor.py` DAG argument binding

### Evaluator & Benchmark Dataset
- **Dataset Path:** `data/eval_public.jsonl`
- **Dataset SHA-256:** `ABDDB7D18A6D8ED908F514A7E560FE4950EBE479EBB2CDB75A7456887C10C6E5`
- **Total Questions:** 100
- **Evaluator:** `benchmark/unified_evaluator.py` (`compute_correctness`, `normalize_answer`)

---

## 2. Invariant Rules
During the 25Q Confidence Run and the Final 100Q Benchmark:
1. No production code changes will be made unless a reproducible systematic defect is discovered.
2. No retrieval, GSQL, embedding, or planner alterations will occur.
3. Bounded retries and fallback budgets will handle transient runtime/provider latency events.
