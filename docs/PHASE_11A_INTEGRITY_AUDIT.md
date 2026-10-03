# Phase 11A — Comprehensive Benchmark Integrity & Agentic Effectiveness Audit Report

**Authoritative Report Version:** 1.0  
**Date:** September 2026  
**Repository:** `d:\Hackathons\TigerGraph`  
**Evaluation Target:** 100-Question Public Olympics Benchmark across RAG, GraphRAG, and Agentic GraphRAG  

---

## 1. Executive Verdict

The Phase 11 three-way benchmark has undergone a rigorous, read-only audit across all 100 questions, underlying source code, database vertices, embedding models, and telemetry trails:

- **Benchmark Integrity Status**: **BENCHMARK VALIDATED — TARGETED ENGINEERING FIXES RECOMMENDED (OUTCOME C)**.
- **Agentic Performance Ground Truth**: Agentic GraphRAG achieves **87/100 (87.0%) Answer Accuracy**, **93/100 (93.0%) Gold Evidence Recall**, and **94/100 (94.0%) Task Completion**.
- **Cross-Pipeline Superiority**:
  - **vs Base RAG**: Net **+68.00% accuracy gain** (+85.00% under strict non-fallback evaluation), **+90.00% evidence gain**, and **2.20x faster operational latency** on completed queries (39.28s vs 86.44s).
  - **vs GraphRAG**: Net **+67.00% accuracy gain** (+85.00% under strict non-fallback evaluation), **+77.00% evidence gain**, and **1.74x faster operational latency** on completed queries (39.28s vs 68.53s).

---

## 2. Embedding-Dimension Resolution

- **Discrepancy Audited**: Phase 11 preflight logs stated `"qwen3-embedding:0.6b — Embedding dim 1536 verified"`, conflicting with the architectural specification of 1024 dimensions.
- **Audit Findings**:
  1. **Ollama Endpoint**: `ollama.embeddings(model="qwen3-embedding:0.6b")` returns an array of length **1024**.
  2. **TigerGraph Schema & Storage**: `DocumentChunk.qwen_embedding` stores a `LIST<DOUBLE>` of size **1024** across all 5,716 chunks.
  3. **HNSW Vector Index**: Configured for dimension **1024** (`vector_index_dim = 1024`).
  4. **Retrieval Implementation**: Encodes query vectors to dimension **1024**.
  5. **Root Cause**: `common/embeddings/embedding_services.py` line 35 contained a fallback default `1536` in `EmbeddingModel.__init__` used when no model config is passed. Native Qwen execution is 100% strictly 1024-dimensional.

---

## 3. Accuracy-Definition Resolution

- **Definition**: Accuracy in Phase 11 is evaluated as **Case-Insensitive Normalized Substring Match** (`compute_normalized_match` in `benchmark/unified_evaluator.py`).
- **Aggregation Fallback Artifact**:
  - Base RAG and GraphRAG reported 18/21 aggregation accuracy.
  - Audit proved that 17 of those 18 matches were **false positives caused by single-digit gold answers matching hex characters in crashed 500 fallback UUID strings** (`"Admin reference ID: ba8051e7-bea6-47b4-9154-947fe896c44d"`).
  - In strict non-fallback evaluation, true RAG aggregation accuracy is **2/21** and GraphRAG is **2/21**.
  - Agentic GraphRAG achieved **21/21 (100.0%)** genuine aggregation accuracy via deterministic TigerGraph GSQL queries.

---

## 4. Retrieval-Intrusion Resolution

- **Discrepancy Audited**: Phase 11 reported 100.0% retrieval intrusion for GraphRAG vs 0.0% for RAG and Agentic.
- **Root Cause**: Evaluator bug in `calculate_retrieval_intrusion` where GraphRAG chunk IDs (`Qxxxx_chunk_0`) were compared directly against gold document IDs (`Qxxxx`) without stripping the `_chunk_\d+` suffix.
- **Corrected Reality**: True non-Olympic document intrusion across all three pipelines is **0.00%**.

---

## 5. Completeness-Definition Resolution

- **Mathematical Formulation**: Word-level token recall:
  $$\text{Completeness} = \frac{|T_{\text{gold}} \cap T_{\text{pred}}|}{|T_{\text{gold}}|}$$
- **Verification**: Verified manually and programmatically across 6 representative question traces (100% exact match against stored values).
- **Defensibility**: The metric is deterministic, bounded in $[0.0, 1.0]$, and mathematically defensible for factual QA.

---

## 6. Token-Definition Resolution

- **Formula**: Strictly additive: $\text{Total Tokens} = \text{Input Tokens} + \text{Output Tokens}$.
- **Populated Averages**:
  - Base RAG: **8,617.17** tokens (N=6 completed queries).
  - GraphRAG: **1,103.30** tokens (N=27 completed queries).
  - Agentic GraphRAG: **7,718.01** tokens (N=94 completed queries).
- **Step Breakdown for Agentic**:
  - Planner: 2,928.44 tokens.
  - Replan: 45.23 tokens.
  - Deterministic Tools (`lookup`, `aggregate`, `superlative`, `temporal`): **0 LLM tokens**.
  - Structural Extraction: 806.59 tokens.
  - Synthesizer: 3,272.82 tokens.

---

## 7. Latency-Definition Resolution

- **Timing Boundary**: Client-side HTTP Round-Trip Time from POST dispatch to response payload reception.
- **Operational Reality on Completed Queries**:
  - Agentic GraphRAG: **39.281 s** ($N=94$).
  - GraphRAG: **68.528 s** ($N=27$).
  - Base RAG: **86.441 s** ($N=6$).
- **Explanation**: Agentic is 2.20x faster than RAG because deterministic GSQL tools execute in milliseconds without multi-thousand-token LLM generation overhead. Naive headline latency (11.289s RAG) was artificially pulled down by 94 failing queries crashing in 2–6s.

---

## 8. Agentic Strategy-Change Resolution

- **Finding**: `strategy_changes = 0` was caused by a telemetry dictionary key omission in `agentic_graph.py` (which logged replanning as `"node": "replan 1"` inside `agent_steps`).
- **Adaptivity Demonstrated**: Trace inspection of 10 representative queries demonstrated genuine dynamic argument chaining (`arg_bindings`, `depends_on`) and real error interception with dynamic replanning (`pub-060`).

---

## 9. Specialist Usage

All 8 registered specialists were audited:
1. `EntityLinkingSpecialist`: 32 invocations, 31 questions (30 success).
2. `GraphTraversalSpecialist`: 32 invocations, 31 questions (30 success, 2 fail).
3. `SimilarityRetrievalSpecialist`: 23 invocations, 22 questions (18 success, 5 fail).
4. `DocumentRetrievalSpecialist`: 23 invocations, 22 questions (23 success).
5. `AnalyticalSpecialist`: 31 invocations, 31 questions (31 success, 0 fail).
6. `MultiHopInvestigationSpecialist`: 21 invocations, 21 questions (21 success, 0 fail).
7. `EvidenceEvaluationSpecialist`: 94 invocations, 94 questions (94 success, 0 fail).
8. `TigerGraphMCPSpecialist`: 0 invocations (direct GSQL tools prioritized for speed).

---

## 10. Cost-Effectiveness Claims

1. **"19 Redundant Planning Overhead"**: **INVALIDATED**. 17 of the 19 RAG matches were false positive hex UUID collisions. Only 2 queries were genuinely solved by both.
2. **"13 Unresolved Multi-Hop"**: **CLARIFIED**. Failures comprise 10 Multi-Hop, 2 Superlative, and 1 Temporal query (6 were 120s HTTP timeouts).

---

## 11. Multi-Hop Failure Table (10 Failed Questions)

| QID | Gold Target | Category | Primary Failure Cause |
| :--- | :--- | :--- | :--- |
| `pub-015` | Dani KingLaura TrottJoanna Rowsell | `other` | 120.0s HTTP client timeout |
| `pub-017` | Yi Siling | `retrieval_miss` | Chunk missed in vector top-k |
| `pub-023` | Hwang Young-Cho | `synthesis` | Synthesis generated generic boilerplate text |
| `pub-060` | Yana Shemyakina | `tool_argument_error` | Missing tool arg; replan exceeded call budget |
| `pub-067` | Rosannagh MacLennan | `synthesis` | Synthesis generated generic boilerplate text |
| `pub-076` | Julia Mancuso | `other` | 120.0s HTTP client timeout |
| `pub-077` | Kaillie Humphries | `other` | 120.0s HTTP client timeout |
| `pub-096` | Fazliddin Gaibnazarov | `other` | 120.0s HTTP client timeout |
| `pub-098` | Bekzat Sattarkhanov | `other` | 120.0s HTTP client timeout |
| `pub-099` | Erik LesserDaniel BöhmArnd PeifferSimon Schempp | `output_formatting` | Unspaced concatenated gold string mismatch |

---

## 12. Superlative Failure Table (2 Failed Questions)

| QID | Gold Target | Category | Primary Failure Cause |
| :--- | :--- | :--- | :--- |
| `pub-004` | Athletics at the 2008 Summer Olympics – Men's marathon | `synthesis_verbatim_title_truncation` | Tool found exact entity; synthesizer rephrased canonical title to natural prose |
| `pub-008` | Sailing at the 2000 Summer Olympics – Soling | `synthesis_verbatim_title_truncation` | Tool found exact entity; synthesizer rephrased canonical title to natural prose |

---

## 13. Accuracy Improvement Recommendation

1. **Synthesizer Canonical Title Preservation**: Add a prompt rule in `base_llm.py` to state official event titles verbatim in bold. Targets 2 Superlative failures.
2. **Client Timeout Extension**: Increase client benchmark HTTP timeout from 120s to 180s in `run_qwen_100_benchmark.py`. Targets 5 Multi-Hop and 1 Temporal failure.
3. **Tool Argument Enforcement**: Ensure planner schema generator enforces non-empty string question arguments. Targets 1 Multi-Hop failure (`pub-060`).

---

## 14. Dashboard Readiness

- **Status**: **READY FOR DASHBOARD CONSTRUCTION (Subject to Audited Metric Definitions)**.
- **Requirements for UI Presentation**:
  - Display both `Accuracy (Normalized Match)` and `Strict Non-Fallback Match`.
  - Display `Operational Latency (Completed Queries)` alongside `Aggregate Latency`.
  - Disaggregate tokens into `Planner`, `Tool LLM`, and `Synthesizer` stages.
  - Zero-cost TigerGraph GSQL tools must be explicitly annotated.
