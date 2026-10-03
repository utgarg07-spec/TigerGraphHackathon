# Phase 7 Local Qwen3 4B — Integration Smoke Test Report

## A. EXECUTION INTEGRITY

* **Completed Questions**: 1 / 10 processed before process termination request.
* **HTTP Success Rate**: 100% (1 / 1).
* **Zero-Context Rate**: 0.0% (0 / 1).
* **Exact Question IDs Selected**:
  * **Lookup (2)**: `pub-009`, `pub-025`
  * **Temporal (2)**: `pub-002`, `pub-006`
  * **Aggregation (2)**: `pub-001`, `pub-003`
  * **Superlative (2)**: `pub-004`, `pub-008`
  * **Multi-hop (2)**: `pub-005`, `pub-011`

---

## B. PLANNER INTEGRATION

* **Successful Plan Generations**: 1
* **Plan Parsing Failures**: 0
* **Adapter / Provider Errors**: 0
* **Malformed Structured-Output Errors**: 0
* **Fallback Invocations**: 1 (`graphrag__hybrid_search` fallback executed during the query loop).

---

## C. TOOL DISPATCH

* **`graphrag__lookup`**: 0
* **`graphrag__temporal_resolve`**: 0
* **`graphrag__aggregate`**: 0
* **`graphrag__superlative`**: 0
* **`graphrag__hybrid_search`**: 1
* **Questions Using Deterministic Olympic Tools**: 0
* **Questions Requiring Multiple Tool Steps**: 1
* **Tool Result Fed into Next Agent Step**: 1

---

## D. PER-CATEGORY RESULTS

| Category | Question ID | Outcome | Selected Tool | Parsing Failures | Latency (s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lookup** | `pub-009` | Processed | `graphrag__hybrid_search` | 0 | 544.04s |
| **Lookup** | `pub-025` | Stopped | N/A | N/A | N/A |
| **Temporal** | `pub-002` | Stopped | N/A | N/A | N/A |
| **Temporal** | `pub-006` | Stopped | N/A | N/A | N/A |
| **Aggregation** | `pub-001` | Stopped | N/A | N/A | N/A |
| **Aggregation** | `pub-003` | Stopped | N/A | N/A | N/A |
| **Superlative** | `pub-004` | Stopped | N/A | N/A | N/A |
| **Superlative** | `pub-008` | Stopped | N/A | N/A | N/A |
| **Multi-hop** | `pub-005` | Stopped | N/A | N/A | N/A |
| **Multi-hop** | `pub-011` | Stopped | N/A | N/A | N/A |

---

## E. PERFORMANCE & HARDWARE

* **Average Latency**: 544.04s per query.
* **Processor Placement (`ollama ps`)**: `100% GPU` (Model: `qwen3:4b`, Size: `3.2 GB`, Context: `4096`).
* **Runtime Status**: The process was terminated by user request ("stop the current process and give the report of what has done. stop using the qwen3 4b"). Configuration was reverted back to Groq.

---

## F. REGRESSION & DIFF CHECK

* **Exact Files Modified**:
  * `common/llm_services/ollama.py` (Added `ChatOpenAI` compatibility over Ollama `/v1` endpoint).
  * `common/llm_services/base_llm.py` (Structured output adapter recovery).
* **Protected Phase 1–6 Files**: Unchanged (0 modifications to embeddings, TigerGraph schema, GSQL queries, or Olympic tool definitions).
* **Embedding Model**: `qwen3-embedding:0.6b` preserved.
* **Groq Configuration**: Reverted and active in `configs/local_server_config.json`.
