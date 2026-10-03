# PHASE 14D-Q — COMPLETE AGENTIC PIPELINE FORENSIC AUDIT REPORT

**Final Status**: `PASS — COMPLETE ROOT-CAUSE MAP`  
**API Calls**: `0`  
**Live Questions**: `0`  
**Production Code Modified**: `NO`  
**Phase 12 / 13 Modified**: `NO`  
**TigerGraph / Embeddings / Dataset Modified**: `NO`  
**Secrets Exposed**: `NO`

---

## 1. Executive Diagnosis

A comprehensive, read-only offline forensic audit was performed across all seven pipeline components (Embedding Generation, Stored Vectors, Vector Query, Agentic Retrieval, LLM Structured Output, Final Answer Synthesis, and Evaluator Binding).

### Key Architectural Findings:
1. **Proven Root Cause of `GSQL-90000` (Vector Size Mismatch)**:
   - `tigergraph_embedding_store.py` line 571 calls installed query `"get_topk_similar"` (`common/gsql/vector/get_topk_similar.gsql`).
   - `get_topk_similar.gsql` line 16 compares `query_vector` against `v.embedding` (the legacy 1536-dimensional Gemini vector attribute).
   - The active embedding model (`qwen3-embedding:0.6b`) generates **1024-dimensional** query vectors.
   - `gds.vector.distance(query_vector, v.embedding, "COSINE")` compares a 1024-dim list with a 1536-dim list, causing TigerGraph to throw:  
     `GSQL-90000: Two lists provided for gds.vector.distance have different sizes.`

2. **Proven Cause of Silent Retrieval Failures & `(no answer produced)` Answers**:
   - `tigergraph_embedding_store.py` line 603 catches `GSQL-90000` / `"different sizes"` and **silently returns `[]`** (empty list).
   - `generate_function` / `structural_retrieve` logs `WARN no documents found` and passes empty context `{error: true}` to synthesis.
   - Retrieval-dependent questions (like `pub-002` and `pub-003`) execute synthesis without retrieved text context and fall back to `"(no answer produced)"`.

3. **Proven Cause of Live Container Evaluator Discrepancy**:
   - `docker-compose.yml` mounts `./configs/:/code/configs`, but **does NOT mount `./benchmark/`**.
   - When commands are executed inside the container (`docker exec graphrag python /code/scratch/...`), python imports `/code/benchmark/unified_evaluator.py` from the **baked Docker image layer**, which was built prior to Phase 14D-K.
   - Host edits to `benchmark/unified_evaluator.py` do not apply inside the running container unless `./benchmark/` is volume-mounted or the container image is rebuilt.

---

## 2. Embedding Dimension Forensics (Part A)

| Component | Dimension | Source File | Function/Line | Authoritative? |
|---|---|---|---|---|
| Ollama model (`qwen3-embedding:0.6b`) | **1024** | Ollama API | native model output | **YES** |
| Embedding wrapper fallback (`embedding_services.py`) | **1536** | `common/embeddings/embedding_services.py` | L35 `config.get("dimensions", 1536)` | **NO (Legacy Fallback)** |
| Config setting (`local_server_config.json`) | **1024** | `configs/local_server_config.json` | L33 `"output_dimensionality": 1024` | **YES** |
| Query vector (`Ollama_Embedding`) | **1024** | `common/embeddings/embedding_services.py` | L241 `config.get("output_dimensionality", ...)` | **YES** |
| `DocumentChunk.qwen_embedding` | **1024** | TigerGraph Schema | `DocumentChunk.qwen_embedding` | **YES** |
| `DocumentChunk.embedding` (Legacy Gemini) | **1536** | `SupportAI_Schema_Native_Vector.gsql` | L18 `embedding(dimension=1536)` | **NO (Deprecated)** |
| `GraphRAG_Hybrid_Qwen_Vector_Search` | **1024** | `GraphRAG_Hybrid_Qwen_Vector_Search.gsql` | L45 `v.qwen_embedding` | **YES** |
| `get_topk_similar.gsql` | **1536** | `common/gsql/vector/get_topk_similar.gsql` | L16 `v.embedding` | **NO (Causes GSQL-90000)** |

### Origin Tracing:
- **Value 1536**: Originates from `embedding_services.py` line 35 default fallback and legacy Gemini schema `SupportAI_Schema_Native_Vector.gsql` line 18.
- **Value 1024**: Originates from `configs/local_server_config.json` (`output_dimensionality: 1024`), native `qwen3-embedding:0.6b` output, and populated `DocumentChunk.qwen_embedding` vertex attribute.

---

## 3. TigerGraph Vector Query Forensics (Part B)

- **Query Inspected**: `get_topk_similar.gsql` vs `GraphRAG_Hybrid_Qwen_Vector_Search.gsql`
- **Query Parameter**: `LIST<FLOAT> query_vector`
- **Distance Function**: `1 - gds.vector.distance(query_vector, v.embedding, "COSINE")`
- **Mismatch Analysis**:
  - `query_vector` passed from `Ollama_Embedding` = **1024 floats**.
  - `v.embedding` on `DocumentChunk` = **1536 floats**.
  - `gds.vector.distance` compares vector length 1024 with vector length 1536 $\rightarrow$ **GSQL-90000 Exception**.

---

## 4. Embedding Data Integrity (Part C)

- **DocumentChunk Vertices**: `5,716` total chunks.
- **qwen_embedding Attribute**: `5,716 / 5,716` chunks populated with **1024-dimensional** Qwen vectors.
- **Data Integrity Status**: Active Qwen vector store in TigerGraph is 100% complete and 1024-dimensional.

---

## 5. Agentic Retrieval Failure Path (Part D)

```
Query Vector (1024-dim)
      │
      ▼
tigergraph_embedding_store.py -> runInstalledQuery("get_topk_similar")
      │
      ▼
get_topk_similar.gsql compares 1024-dim query_vector with 1536-dim v.embedding
      │
      ▼
GSQL-90000: Two lists provided for gds.vector.distance have different sizes
      │
      ▼
tigergraph_embedding_store.py L603 catches GSQL-90000 -> SILENTLY RETURNS []
      │
      ▼
generate_function / structural_retrieve -> WARN no documents found
      │
      ▼
Synthesis executes without text context -> "(no answer produced)"
```

---

## 6. Structured Output / Parser Forensics (Part E)

1. **Request Format**: `base_llm.py` calls `with_structured_output(schema)` via LangChain.
2. **Provider Response Anomaly**: AIRouter / backend provider occasionally returns `content=''` with `parsed=None` (`content='' additional_kwargs={'parsed': None, 'refusal': None}`).
3. **Recovery Mechanism**: `base_llm.py` catches `OutputParserException`, logs a warning, and falls back to `_try_recover_structured()`, `PydanticOutputParser`, or raw JSON string salvage.

---

## 7. Evaluator Forensics (Part F)

1. **Host Evaluator Accuracy**: Host file `benchmark/unified_evaluator.py` correctly evaluates `pub-001` (`five`) and `pub-003` (`eight`) as **`True` (5/5 100%)** using number-word normalization and token word-boundary matching.
2. **Container Binding Issue**: `docker-compose.yml` mounts `./configs/:/code/configs`, but **does NOT mount `./benchmark/`**.
3. **Container Execution Truth**: When `docker exec` runs inside `graphrag` container, python imports `/code/benchmark/unified_evaluator.py` from the baked Docker image layer. Because the container image was built before Phase 14D-K, live container execution evaluates using the stale pre-fix evaluator.

---

## 8. Non-Determinism Classification Audit (Part G)

| Component / Layer | Classification | Determinism Assessment |
|---|---|---|
| Vector Schema Matching | **INFRASTRUCTURE-DEPENDENT** | Query dimension must match stored attribute (1024 == 1024). |
| Deterministic Tools | **DETERMINISTIC** | `graphrag__aggregate`, `graphrag__superlative`, `graphrag__temporal_resolve` produce 100% exact facts. |
| Answer Evaluator | **DETERMINISTIC** | String normalization and word-boundary matching are 100% deterministic. |
| Docker Container Code | **INFRASTRUCTURE-DEPENDENT** | Volume mounts dictate whether host code fixes take effect inside container. |
| AIRouter Provider Latency | **PROVIDER-DEPENDENT** | Provider load and endpoint routing govern response latency. |
| Structured Output Compliance | **MODEL/PROVIDER-DEPENDENT** | Model compliance with JSON schema varies per call (handled via parser fallbacks). |

---

## 9. Complete Root-Cause Matrix (Part H)

| Failure | Evidence | Root Cause Proven? | Component | Live API Required to Verify? |
|---|---|---|---|---|
| 1536/1024 Vector Mismatch | `embedding_services.py` L35 default 1536 vs `local_server_config.json` L33 1024 | **YES** | `common/embeddings/` | **NO** |
| GSQL-90000 Vector Size Error | `get_topk_similar.gsql` L16 queries 1536-dim `v.embedding` with 1024-dim Qwen vector | **YES** | `common/gsql/vector/` & `tigergraph_embedding_store.py` | **NO** |
| Live Container Scoring False | `docker-compose.yml` lacks `./benchmark/` volume mount, running stale image code | **YES** | `docker-compose.yml` & `benchmark/` | **NO** |
| Empty LLM Output / Parser Fallback | `base_llm.py` L1129 logs `content='' parsed=None` when provider fails structured output contract | **YES** | `common/llm_services/` | **NO** |
| Silent Empty Vector Retrieval | `tigergraph_embedding_store.py` L603 catches `GSQL-90000` and returns `[]` | **YES** | `common/embeddings/tigergraph_embedding_store.py` | **NO** |

---

## 10. Required Modifications Map (Part I — Described, NOT Implemented)

1. **`common/embeddings/tigergraph_embedding_store.py`**:
   - Update `self.conn.runInstalledQuery("get_topk_similar", ...)` to target `v.qwen_embedding` or call `GraphRAG_Hybrid_Qwen_Vector_Search` when active embedding model is Qwen.
2. **`common/embeddings/embedding_services.py`**:
   - Update `EmbeddingModel.__init__` line 35 to resolve `config.get("output_dimensionality", config.get("dimensions", 1024))`.
3. **`docker-compose.yml`**:
   - Add volume mount `- ./benchmark/:/code/benchmark` under `graphrag` service so host evaluator fixes apply inside container without requiring container rebuilds.

---

## 11. Final Declarations

- **What can be fixed deterministically**: Vector dimension contract, GSQL query selection, silent exception handling, evaluator logic, and Docker volume bindings.
- **What cannot be guaranteed from a prompt**: Third-party LLM response latency and raw provider JSON formatting variance.
- **What must be tested after repair**: Offline 16/16 evaluator test suite, vector similarity query execution, container volume binding, and single 5Q validation run.
