# PHASE 14D-R — DETERMINISTIC PIPELINE CONTRACT REPAIR

**Status**: `PASS — DETERMINISTIC CONTRACTS REPAIRED`  
**Mode**: `IMPLEMENTATION + OFFLINE VALIDATION ONLY`  
**API Calls**: `0`  
**Live Questions Executed**: `0`  

---

## Executive Summary

Phase 14D-R executed the controlled implementation and offline validation of all 4 deterministic engineering defects identified in the Phase 14D-Q forensic report. No live API calls, benchmark question executions, or model downloads were performed.

---

## 1. Root Causes Addressed

1. **FIX A — Qwen Vector Retrieval Contract**:
   - **Issue**: 1024-dimensional Qwen query vectors were passed to `get_topk_similar.gsql`, which compared them against 1536-dimensional legacy `v.embedding`, directly causing `GSQL-90000: Two lists provided for gds.vector.distance have different sizes`.
   - **Fix**: Modified `retrieve_similar_with_score` in [`common/embeddings/tigergraph_embedding_store.py`](file:///d:/Hackathons/TigerGraph/common/embeddings/tigergraph_embedding_store.py) to detect 1024-dimensional query vectors and route them to `GraphRAG_Hybrid_Qwen_Vector_Search` operating on `v.qwen_embedding` (1024-d).

2. **FIX B — Legacy 1536 Fallback Removal**:
   - **Issue**: `EmbeddingModel.__init__` defaulted `dimensions` to 1536 even when configured for Qwen.
   - **Fix**: Updated `EmbeddingModel.__init__` in [`common/embeddings/embedding_services.py`](file:///d:/Hackathons/TigerGraph/common/embeddings/embedding_services.py) to prioritize explicit `output_dimensionality` first and default to 1024 for standard/Qwen embeddings, while maintaining explicit 1536 for legacy `GenAI_Embedding`.

3. **FIX C — Retrieval Error Observability**:
   - **Issue**: `tigergraph_embedding_store.py` caught GSQL query execution exceptions and returned `[]`, turning real database vector failures into false "zero documents found".
   - **Fix**: Updated `retrieve_similar_with_score` to re-raise vector/GSQL execution failures as explicit `RuntimeError` instances so callers and telemetry can distinguish vector query failures from genuine empty search results.

4. **FIX D — Container Evaluator Consistency**:
   - **Issue**: `docker-compose.yml` did not mount `./benchmark/`, causing live containers to run stale baked image code instead of the validated host evaluator.
   - **Fix**: Added `./benchmark/:/code/benchmark` volume mount under `graphrag` service in [`docker-compose.yml`](file:///d:/Hackathons/TigerGraph/docker-compose.yml).

---

## 2. Modified Production Files & Functions

| File Path | Modified Function / Section | Change Description |
| :--- | :--- | :--- |
| [`common/embeddings/tigergraph_embedding_store.py`](file:///d:/Hackathons/TigerGraph/common/embeddings/tigergraph_embedding_store.py) | `retrieve_similar_with_score` | Route 1024-d query vectors to `GraphRAG_Hybrid_Qwen_Vector_Search`; raise `RuntimeError` on GSQL failures. |
| [`common/embeddings/embedding_services.py`](file:///d:/Hackathons/TigerGraph/common/embeddings/embedding_services.py) | `EmbeddingModel.__init__` | Resolve `output_dimensionality` first; default standard/Qwen to 1024; preserve GenAI 1536. |
| [`docker-compose.yml`](file:///d:/Hackathons/TigerGraph/docker-compose.yml) | `services.graphrag.volumes` | Mount `./benchmark/:/code/benchmark`. |

---

## 3. Before/After Contract Comparisons

### Retrieval Query Routing
- **Before**: `Qwen (1024-d vector)` -> `get_topk_similar.gsql` -> `v.embedding (1536-d)` -> `GSQL-90000` -> `swallowed` -> `[]`
- **After**: `Qwen (1024-d vector)` -> `GraphRAG_Hybrid_Qwen_Vector_Search.gsql` -> `v.qwen_embedding (1024-d)` -> `real document matches`

### Embedding Dimension Resolution
- **Before**: `config.get("dimensions", 1536)` (forced legacy 1536)
- **After**: `output_dimensionality` (`1024`) -> `dimensions` setting -> `1024` default (Qwen/standard)

### Retrieval Error Handling
- **Before**: `catch Exception -> return []` (masked infrastructure failures)
- **After**: `catch Exception -> raise RuntimeError("TigerGraph vector query failed: ...")` (explicit observability)

### Docker Evaluator Synchronization
- **Before**: Container runs stale baked `/code/benchmark/unified_evaluator.py`.
- **After**: Container shares host `./benchmark/:/code/benchmark` volume.

---

## 4. Offline Validation Suite Results

1. **`py_compile` Check**: `PASS`
   - `common/embeddings/tigergraph_embedding_store.py`
   - `common/embeddings/embedding_services.py`
   - `scratch/test_phase14d_r_contracts.py`

2. **Evaluator Unit Test Suite**: `16/16 PASS`
   - Verified word-number normalization and answer score evaluation.

3. **Phase 14D-R Vector Contract Test Suite**: `5/5 PASS`
   - `test_01_embedding_dimension_fallback`: PASS (Qwen=1024, Default=1024, GenAI=1536)
   - `test_02_qwen_vector_retrieval_routing`: PASS (1024-d routes to `GraphRAG_Hybrid_Qwen_Vector_Search`)
   - `test_03_retrieval_error_not_swallowed`: PASS (GSQL failures raise explicit `RuntimeError`)
   - `test_04_docker_compose_volume_mount`: PASS (Verified `./benchmark/:/code/benchmark`)
   - `test_05_static_check_legacy_embedding_untouched`: PASS (`DocumentChunk.embedding` 1536 untouched)

4. **Integrity & Compliance Checks**:
   - `benchmark_questions_modified`: `False`
   - `phase12_phase13_artifacts_modified`: `False`
   - `dataset_or_embeddings_mutated`: `False`
   - `api_calls`: `0`
   - `live_questions`: `0`

---

## Final Status

`PASS — DETERMINISTIC CONTRACTS REPAIRED`
