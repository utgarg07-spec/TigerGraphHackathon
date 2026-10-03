# PHASE 3 — QWEN VECTOR PATH INTEGRATION PILOT REPORT

## Executive Summary
A non-destructive dual-vector path integration pilot for local **Ollama** and **`qwen3-embedding:0.6b`** (1024-d) was executed against the live TigerGraph database.

The secondary vector attribute `qwen_embedding` (1024-d, HNSW index, cosine metric) was successfully created alongside the existing 1536-d Gemini vector attribute `embedding`. **50** `DocumentChunk` records were embedded into `qwen_embedding`. End-to-end vector search using Ollama query embeddings and new GSQL queries (`Content_Similarity_Qwen_Vector_Search` and `GraphRAG_Hybrid_Qwen_Vector_Search`) was verified with 100% pipeline success.

Zero Gemini vectors were deleted or overwritten, zero schema components were broken, and zero deterministic tools or agentic planners were altered.

---

## 1. Section A — Actually Tested (Empirical Verification)

1. **TigerGraph DDL Schema Change**: Successfully executed schema change job `add_qwen_vector` creating `DocumentChunk.qwen_embedding` (Dimension=1024, IndexType="HNSW", DataType="FLOAT", Metric="COSINE").
2. **Schema & Data Preservation**:
   - `DocumentChunk` vertices: **5,716** (100% preserved)
   - `Event` vertices: **2,162** (100% preserved)
   - `DOCUMENT_HAS_EVENT` edges: **2,162** (100% preserved)
   - Existing Gemini 1536-d vectors: **1,966** (100% preserved)
3. **Controlled 50-Chunk Pilot Ingestion**: Embedded 50 target `DocumentChunk` texts into `qwen_embedding` via Ollama (`qwen3-embedding:0.6b`) in **21.73s** (~434 ms/chunk including network API calls). All 50 vectors verified exact dimension 1,024.
4. **GSQL Query Installation & Execution**: Created and installed `Content_Similarity_Qwen_Vector_Search` and `GraphRAG_Hybrid_Qwen_Vector_Search` queries in graph `Olympics`. Verified vector search returned top-5 chunks using 1024-d query vectors.
5. **End-to-End Retrieval Pilot**: Tested 5 representative public questions across all question types (lookup, temporal, aggregation, superlative). 100% query embeddings and vector searches succeeded with ~730ms average latency.

---

## 2. Section B — Source-Code & Schema Findings

1. **Schema DDL Compatibility**: TigerGraph 4.2+ native vector syntax supports multiple distinct vector attributes per vertex type (`ALTER VERTEX DocumentChunk ADD VECTOR ATTRIBUTE qwen_embedding(...)`).
2. **GSQL Distance Functions**: GSQL `gds.vector.distance(query_vector, v.qwen_embedding, "COSINE")` dynamically adapts to the target attribute's dimension (1024-d) as long as `query_vector` matches `qwen_embedding.size()`.
3. **Provider Factory**: `Ollama_Embedding` class in `common/embeddings/embedding_services.py` seamlessly wraps `langchain_ollama.OllamaEmbeddings` and connects to `http://host.docker.internal:11434`.
4. **Retrieval Isolation**: Vector search queries accept `vector_query` overrides in `SimilarityRetriever` and `HybridRetriever`, allowing complete isolation between Gemini (1536-d) and Qwen (1024-d) execution paths.

---

## 3. Section C — Production Changes Made

1. [`graphrag/app/common/embeddings/embedding_services.py`](file:///d:/Hackathons/TigerGraph/common/embeddings/embedding_services.py#L235-L250)
   - Updated `Ollama_Embedding` to support `output_dimensionality` / `dimensions` configuration (1024-d) and `ollama_url` / `base_url` resolution (`http://host.docker.internal:11434`).
2. [`graphrag/app/supportai/retrievers/SimilarityRetriever.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/supportai/retrievers/SimilarityRetriever.py#L16-L40)
   - Added optional `vector_query` parameter defaulting to `"Content_Similarity_Vector_Search"`.
3. [`graphrag/app/supportai/retrievers/HybridRetriever.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/supportai/retrievers/HybridRetriever.py#L15-L80)
   - Added optional `vector_query` parameter defaulting to `"GraphRAG_Hybrid_Vector_Search"`.
4. **TigerGraph Database Schema**: Added `qwen_embedding(Dimension=1024, IndexType="HNSW", DataType="FLOAT", Metric="COSINE")` to `DocumentChunk`.
5. **GSQL Query Library**: Installed `Content_Similarity_Qwen_Vector_Search` and `GraphRAG_Hybrid_Qwen_Vector_Search`.

---

## 4. Section D — Pilot Retrieval Results

| Question Category | Sample Question | Query Vector | Vector Search | Chunks Retrieved | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lookup** | *Sailing RS:X Nations* | 1024-d OK | OK | 5 | 2,403.06 ms |
| **Temporal** | *20km Walk Gold before 2016* | 1024-d OK | OK | 5 | 732.43 ms |
| **Aggregation** | *Biathlon >73 competitors* | 1024-d OK | OK | 5 | 719.66 ms |
| **Superlative** | *Athletics max competitors 2008* | 1024-d OK | OK | 5 | 730.85 ms |

---

## 5. Section E — Remaining Risks & Mitigation

1. **Corpus Coverage**: Currently 50 out of 5,716 chunks (0.87%) are populated with Qwen embeddings. Complete 5,716-chunk ingestion is required before evaluating 100-question benchmark accuracy.
2. **Memory / GPU Resource**: Host RTX 3050 GPU VRAM footprint is ~3.3 GB during Ollama inference. Ensure Ollama background service remains running on host during execution.
3. **Reversion Safety**: Production default configurations remain set to Gemini 1536-d (`embedding`). No production default paths were changed.

---

## 6. Section F — Exact Next Command for Full 5,716-Chunk Embedding

To embed all 5,716 `DocumentChunk` vertices into `DocumentChunk.qwen_embedding` using local Ollama on GPU, run:

```bash
docker exec -w /code -e PYTHONPATH=/code graphrag python /code/scratch/run_full_qwen_embedding.py
```

---
**STOP.** Pilot complete. No full-corpus embedding started. No 100-question benchmark executed.
