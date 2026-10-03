# Project Context Recovery & Audit Report

**Date**: September 24, 2026  
**Status**: AUDIT COMPLETE (Read-Only Recovery)  
**Context**: Reconstructed project state following post-Phase 5 computer shutdown.  

---

## A. Runtime State

- **Docker Containers**:
  - `graphrag` (`tigergraph/graphrag:latest`): **UP** (Port 8000)
  - `graphrag-ui` (`tigergraph/graphrag-ui:latest`): **UP** (Port 3000)
  - `graphrag-ecc` (`tigergraph/graphrag-ecc:latest`): **UP** (Port 8001)
  - `chat-history` (`tigergraph/chat-history:latest`): **UP** (Port 8002)
- **Ollama Runtime**:
  - Endpoint: `http://localhost:11434` / `http://host.docker.internal:11434`
  - Status: **REACHABLE & OPERATIONAL**
  - Model Available: `qwen3-embedding:0.6b`
  - Output Vector Dimensions: **1024-d** (Verified via test embedding generation)
- **TigerGraph Cloud Connection**:
  - Host: `https://tg-eb6a2e24-db15-4708-b294-710c9f6af79b.tg-2635877100.i.tgcloud.io`
  - Graph: `Olympics`
  - RESTPP / GS Ports: `443`
  - Authentication: Valid secret & active token

---

## B. Repository State

- **Git Branch**: `main`
- **Latest Commit**: `3fff41f` (*Complete document migration and controlled embedding test*)
- **Git Status**: 10 Modified files, 24 Untracked files

### Modified Files Breakdown:
1. `common/embeddings/embedding_services.py`: Added `qwen3-embedding:0.6b` 1024-d Ollama embedding support.
2. `common/embeddings/tigergraph_embedding_store.py`: Added handling for GSQL-90000 vector size mismatch exceptions.
3. `configs/server_config.json`: Configured database connection to TigerGraph Cloud and embedding service to Ollama 1024-d Qwen.
4. `graphrag/app/agent/agent_graph.py`: Added query dispatch routing for Qwen 1024-d queries.
5. `graphrag/app/supportai/retrievers/HybridRetriever.py`: Added vector_query parameter and Qwen query name auto-routing (`GraphRAG_Hybrid_Qwen_Vector_Search`).
6. `graphrag/app/supportai/retrievers/SimilarityRetriever.py`: Added vector_query parameter and Qwen similarity query auto-routing (`Content_Similarity_Qwen_Vector_Search`).
7. `graphrag/app/tools/graphrag_tools.py`: Updated hybrid and similarity search tool helpers to select Qwen vector queries dynamically.
8. `graphrag/app/tools/olympic_tools.py`: Standardized citation structure to `{"id": f"Event/{event_id}"}` matching StepResult Pydantic schema.
9. `graphrag/app/tools/test_olympic_tools.py`: Made dataset loader paths robust across local and Docker execution.
10. `graphrag/app/tools/tool_registry.py`: Added automatic invocation of `register_olympic_tools()` on import.

---

## C. TigerGraph Live Graph Audit

| Metric | Target / Requirement | Live Graph Audit Result | Status |
|---|---|---|---|
| **Total `DocumentChunk` Vertices** | 5,716 | **5,716** | **PASSED** |
| **`qwen_embedding` (1024-d)** | 5,716 | **5,716 (100%)** | **PASSED** |
| **Gemini `embedding` (1536-d)** | 1,966 | **1,966 (Preserved)** | **PASSED** |
| **Total `Event` Vertices** | 2,162 | **2,162** | **PASSED** |
| **`DOCUMENT_HAS_EVENT` Edges** | 2,162 | **2,162** | **PASSED** |
| **Qwen Vector Index / Schema** | Present | **`EmbeddingAttributes`: `qwen_embedding` (1024-d COSINE HNSW)** | **PASSED** |
| **`GraphRAG_Hybrid_Qwen_Vector_Search`** | Installed | **INSTALLED** | **PASSED** |
| **`Content_Similarity_Qwen_Vector_Search`** | Installed | **INSTALLED** | **PASSED** |

---

## D. Phase 0–7 Status Matrix

| Phase | Description | Status | Evidence File(s) | Key Metrics / Outcome |
|---|---|---|---|---|
| **Phase 0** | Infrastructure & Project Setup | **Completed** | `configs/server_config.json` | Docker services up, TigerGraph Cloud connected. |
| **Phase 1** | Document Chunking | **Completed** | `benchmark/results/phase3_full_corpus_chunk_prep_report.md` | 5,716 `DocumentChunk` vertices created. |
| **Phase 2** | Gemini Baseline Vector Ingestion | **Completed** | `benchmark/results/local_embedding_evaluation_report.md` | 1,966 chunks embedded with 1536-d Gemini vectors before API quota exhaustion. |
| **Phase 3** | Qwen 1024-d Migration & Full Embedding | **Completed** | `benchmark/results/qwen_final_embedding_repair_report.md` | 5,716/5,716 (100%) chunks embedded with `qwen3-embedding:0.6b` 1024-d vectors. |
| **Phase 4** | Deterministic Event Graph Construction | **Completed** | `graph/validation/validate_phase4.py` | 2,162 `Event` vertices, 2,162 `DOCUMENT_HAS_EVENT` edges. |
| **Phase 5** | 100-Question Qwen Hybrid Benchmark | **Completed** | `benchmark/results/phase5_qwen_hybrid_100_question_benchmark_report.md` | 100/100 HTTP successes, 16.0% gold doc recall, 73% zero-context (un-fallback hybrid). |
| **Phase 6** | Deterministic Olympic Tool Suite | **Completed** | `graphrag/app/tools/test_olympic_tools.py` | **78/78 tests passed (100% accuracy)** across lookup, aggregate, superlative, temporal. |
| **Phase 7** | Agentic Integration Preparation | **Preparation Complete** | `benchmark/results/phase7_agentic_integration_prep_report.md` | 4 Olympic tools auto-registered in `tool_registry.py` (catalog expanded from 8 to 12 tools). |

---

## E. Phase 3 Benchmark Reconciliation

### Discrepancy Investigation
- **Reported in Phase 5 Report (Section F)**: "Phase 3 Gold Document Recall = 21.0% (21/100)"
- **Reported in Phase 3 Benchmark Summary**: "Gold Document Retrieval Hit Rate = 3.0% (3/100)"

### Empirical Findings:
1. **JSONL Ground Truth**:
   - Source: `benchmark/results/phase3_qwen_100_benchmark.jsonl` and `benchmark/results/phase3_qwen_100_benchmark_summary.json`.
   - `gold_retrieval_hit_count` = **3 / 100 (3.0%)**.
   - `normalized_match_count` = **19 / 100 (19.0%)**.
   - Gold hits occurred exclusively in 3 queries: `pub-002` (Temporal), `pub-004` (Superlative), `pub-008` (Superlative).
2. **Calculation Details**:
   - **Numerator**: 3 questions where `retrieved_doc_ids` contained at least one ID from `gold_doc_ids`.
   - **Denominator**: 100 total benchmark questions.
   - **Calculation**: $\frac{3}{100} = 3.0\%$.
3. **Reason for Discrepancy**:
   - The Phase 5 markdown report narrative erroneously cited 21.0% by either adding `normalized_match_count` (19%) or referencing an informal draft calculation prior to JSONL finalization.
   - **Authoritative Value**: **3.0% (3/100)** for Phase 3 pure vector retrieval hit rate.

---

## F. Phase 5 Benchmark Reconciliation

- **File Verified**: `benchmark/results/phase5_qwen_hybrid_100_benchmark_summary.json`
- **Total Questions Executed**: 100 / 100 (100.0% HTTP Success, 0 Errors)
- **Model Config**: Ollama `qwen3-embedding:0.6b` (1024-d) + Groq LLM (`openai/gpt-oss-20b`)
- **Query Executed**: `GraphRAG_Hybrid_Qwen_Vector_Search`
- **Pass QType**: `False`
- **Overall Gold Document Recall**: **16 / 100 (16.0%)**
- **Zero-Context Rate**: **73 / 100 (73.0%)**
- **Per-QType Recall Breakdown**:
  - Temporal (22 questions): **54.55%** (12/22 hits, 0 zero-context queries)
  - Multi-Hop (28 questions): **10.71%** (3/28 hits, 14 zero-context queries)
  - Lookup (19 questions): **5.26%** (1/19 hits, 18 zero-context queries)
  - Aggregation (21 questions): **0.00%** (0/21 hits, 21 zero-context queries)
  - Superlative (10 questions): **0.00%** (0/10 hits, 10 zero-context queries)
- **Root Cause of Zero-Context**:
  - `GraphRAG_Hybrid_Qwen_Vector_Search` requires traversing `DOCUMENT_HAS_EVENT` edges from seed chunks. Chunks without outgoing graph edges (out-degree = 0) are discarded, yielding zero context.
  - In Phase 7 Agentic mode, structured questions (Lookup, Aggregation, Superlative, Temporal) are handled deterministically by Phase 6 tools rather than relying on pure chunk graph traversal.

---

## G. Phase 4 / 6 / 7 Integration Status

1. **Phase 4 (Graph Structures)**:
   - 2,162 `Event` vertices and 2,162 `DOCUMENT_HAS_EVENT` edges fully populated and linked in TigerGraph Cloud.
2. **Phase 6 (Deterministic Tools)**:
   - All 4 tools (`graphrag__lookup`, `graphrag__aggregate`, `graphrag__superlative`, `graphrag__temporal_resolve`) passed **78/78 (100%) test cases** in `graphrag/app/tools/test_olympic_tools.py`.
3. **Phase 7 (Planner Catalog & Visibility)**:
   - `tool_registry.py` automatically registers the 4 Olympic tools on import.
   - Planner catalog expanded from 8 tools to **12 registered tools**.
   - Tools are **fully visible to and callable by** the LLM planner and `agentic_executor.py`.

---

## H. Exact Next Gate

1. **What is already complete?**
   - Phases 0, 1, 2, 3, 4, 5, 6, and Phase 7 integration preparation are 100% complete and verified.
2. **What is actually blocking Phase 7?**
   - Phase 7 is **NOT blocked**. Integration preparation is complete.
3. **Phase 5 Data Repair Required?**
   - **NO**. All 5,716 `DocumentChunk` vertices contain valid 1024-d Qwen vectors. No database or embedding repairs are required.
4. **Missing Hybrid Vector Fallback Decision**:
   - `HybridRetriever.py` does not fallback to pure vector search when graph traversal returns 0 context.
   - For Phase 7, the 4 deterministic tools handle the exact structured question types that failed graph traversal in Phase 5. Unstructured queries utilize hybrid or vector tools as selected by the planner.
5. **Phase 7 Benchmark Settings**:
   - Standard Phase 7 benchmark will run with `pass_qtype=False` (relying on LLM planner dynamic routing).
6. **Completion Model**:
   - Current completion service: Groq LLM (`openai/gpt-oss-120b` in `server_config.json` / `openai/gpt-oss-20b` in `local_server_config.json`).
7. **Architecture Readiness**:
   - Phase 7 can run using the existing Qwen embeddings + hybrid retrieval + 12-tool registry without further architectural modifications.

---

## I. Files That Should NOT Be Modified

To preserve system stability and benchmark integrity, the following files MUST NOT be modified prior to explicit user direction:

- `common/embeddings/embedding_services.py`
- `common/embeddings/tigergraph_embedding_store.py`
- `common/gsql/supportai/retrievers/GraphRAG_Hybrid_Qwen_Vector_Search.gsql`
- `graphrag/app/supportai/retrievers/HybridRetriever.py`
- `graphrag/app/supportai/retrievers/SimilarityRetriever.py`
- `graphrag/app/tools/olympic_tools.py`
- `graphrag/app/tools/tool_registry.py`
- `configs/server_config.json`
- `configs/local_server_config.json`
