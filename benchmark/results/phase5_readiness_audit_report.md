# Phase 5 — Graph RAG Baseline Readiness Audit Report

**Date**: 2026-09-20  
**Audit Target**: `mode=classic` + `rag_method=hybridsearch`  
**Decision**: **B. BLOCKED BY PHASE 3**  

---

## 1. Executive Summary

This readiness audit evaluated whether the existing repository pipeline (`mode=classic`, `rag_method=hybridsearch`) can execute correctly against the Phase 4 deterministic Olympic graph without requiring the incomplete Phase 3 `DocumentChunk` embedding pipeline or Gemini API calls.

**Key Finding**: `classic + hybridsearch` **CANNOT** run in the current state. It has a hard, mandatory dependency on generating query embeddings via Gemini (`embed_query`) AND on TigerGraph `DocumentChunk.embedding` vector similarity matching (`WHERE v.embedding.size() > 0`). It does not query or utilize the Phase 4 Olympic Event graph.

---

## 2. TASK 1 — Execution Path Trace (`classic` + `hybridsearch`)

1. **API Endpoint**: `POST /{graphname}/query` in [`graphrag/app/routers/inquiryai.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/routers/inquiryai.py#L79).
2. **Router & Agent Construction**:
   - `retrieve_answer()` parses `query: NaturalLanguageQuery` with `mode="classic"` and `rag_method="hybridsearch"`.
   - `_chat_agent(...)` in [`graphrag/app/routers/ui.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/routers/ui.py#L2924) resolves engine to `classic` and retriever to `hybridsearch`.
   - `make_agent(...)` in [`graphrag/app/agent/agent.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/agent/agent.py#L280) instantiates `TigerGraphAgent(supportai_retriever="hybridsearch")`.
3. **Graph Execution**:
   - `TigerGraphAgentGraph.question_for_agent()` executes state graph node `retrieve_sources()`.
   - `_dispatch_retriever("hybridsearch", state)` in [`graphrag/app/agent/agent_graph.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/agent/agent_graph.py#L410) invokes `self.hybrid_search(state)`.
4. **Retriever Core**:
   - `HybridRetriever(embedding_model, embedding_store, llm_provider, connection)` in [`graphrag/app/supportai/retrievers/HybridRetriever.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/supportai/retrievers/HybridRetriever.py#L5) is instantiated.
   - `HybridRetriever.search()` executes:
     1. `query_vector = self._generate_embedding(question)` in [`BaseRetriever.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/supportai/retrievers/BaseRetriever.py#L178), which calls Gemini `embed_query(question)`.
     2. Calls installed GSQL query `conn.runInstalledQuery("GraphRAG_Hybrid_Vector_Search", params={"query_vector": query_vector, ...})`.
5. **GSQL Query Execution**:
   - In [`GraphRAG_Hybrid_Vector_Search.gsql`](file:///d:/Hackathons/TigerGraph/common/gsql/supportai/retrievers/GraphRAG_Hybrid_Vector_Search.gsql#L47), Line 47 selects seed chunks: `SELECT v FROM vset:v WHERE v.embedding.size() > 0 POST-ACCUM @@topk_set += Similarity_Results(v, 1 - gds.vector.distance(query_vector, v.embedding, "COSINE"))`.
6. **Missing Embedding Impact**:
   - Calling Gemini `embed_query` fails due to exhausted quota.
   - Even if query vector generation is bypassed, 0 out of 229 `DocumentChunk` vertices in TigerGraph have non-empty embeddings (`WHERE v.embedding.size() > 0`), causing GSQL seed selection to return 0 chunks.

---

## 3. TASK 2 — Hard Dependencies Audit

| Component | Required by hybridsearch? | Current State | Blocking? |
| :--- | :--- | :--- | :--- |
| **Document vertices** | Yes (parent document target) | 2,162 vertices exist in TigerGraph | No |
| **DocumentChunk vertices** | Yes (seed chunk search target) | 229 vertices exist (incomplete; 2,162 expected) | **YES** |
| **DocumentChunk.embedding** | **Yes (mandatory for seed selection `v.embedding.size() > 0`)** | **0 / 229 have embeddings** | **YES** |
| **Vector index / GDS vector distance** | **Yes (`gds.vector.distance(query_vector, v.embedding, "COSINE")`)** | **Unavailable (no chunk embeddings in DB)** | **YES** |
| **Entity / Relationship graph** | Optional (graph expansion hops) | Entity extraction switch is disabled (`false`) | No |
| **Olympic Event graph** | No (hybridsearch queries `DocumentChunk`, not `Event`) | 2,162 `Event` vertices exist (Phase 4 complete) | No (not queried by hybridsearch) |
| **Hybrid retrieval GSQL queries** | Yes (`GraphRAG_Hybrid_Vector_Search.gsql`) | Installed & available in TigerGraph | No |
| **LLM synthesis** | Yes (Groq `openai/gpt-oss-120b` generates final answer) | Configured & operational | No |

---

## 4. TASK 3 — Controlled Query Decision

- **Execution Attempt**: **NOT ATTEMPTED / BYPASSED (Safety Constraint Enforced)**
- **Reason**: `HybridRetriever.search()` calls `self._generate_embedding(question)`, which triggers a live call to Gemini API (`embed_query`). Performing this call would violate the audit directive (*"DO NOT call Gemini"*). Furthermore, because `v.embedding.size() > 0` evaluates to false for all existing `DocumentChunk` vertices, GSQL seed retrieval produces an empty context.

---

## 5. TASK 4 — Comparison: `similaritysearch` vs `hybridsearch`

- Both `classic + similaritysearch` (`SimilarityRetriever`) and `classic + hybridsearch` (`HybridRetriever`) **depend on the exact same vector index and embedding infrastructure**.
- Both call `_generate_embedding(question)` via `BaseRetriever.py`, which invokes Gemini `embed_query`.
- Both pass `query_vector` to GSQL queries (`Content_Similarity_Vector_Search` and `GraphRAG_Hybrid_Vector_Search`) that require `WHERE v.embedding.size() > 0`.
- Neither method queries the Phase 4 deterministic Olympic `Event` graph vertices.
- **Conclusion**: Both classic retrieval methods are equally blocked by the incomplete Phase 3 vector embedding pipeline.

---

## 6. TASK 5 — Final Decision

### **B. BLOCKED BY PHASE 3**

**Detailed Justification**:
`classic + hybridsearch` cannot run against the currently available graph data because:
1. `HybridRetriever` requires invoking Gemini API to embed the user's question (`embed_query`), which is blocked by exhausted Gemini quota.
2. The GSQL query `GraphRAG_Hybrid_Vector_Search` has a hard requirement for non-empty `DocumentChunk.embedding` attributes in TigerGraph to populate its seed set (`WHERE v.embedding.size() > 0`). Currently, 0 / 229 `DocumentChunk` vertices have non-empty embeddings.
3. `hybridsearch` operates over `DocumentChunk` text vectors, not over the Phase 4 `Event` graph vertices. The deterministic Olympic graph built in Phase 4 is queried via the Phase 6 tool layer (`graphrag__lookup`, `graphrag__aggregate`, `graphrag__superlative`, `graphrag__temporal_resolve`), which is deliberately kept out of classic retrieval and planner catalog visibility.
