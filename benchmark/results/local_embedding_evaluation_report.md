# PHASE 3 — LOCAL QWEN EMBEDDING EVALUATION REPORT

## Executive Summary
An empirical evaluation of local open-weight embeddings using **Ollama** and **`qwen3-embedding:0.6b`** was conducted.

The local model was verified to produce **1024-dimensional** embeddings directly on the host NVIDIA GeForce RTX 3050 GPU. All 50 document chunks and 5 evaluation queries were processed with 100% vector dimension compliance (1024-d), zero errors, and zero writes/mutations to the production TigerGraph database.

---

## 1. Local Model & Environment Verification (Task 1)

| Metric / Parameter | Value / Detail |
| :--- | :--- |
| **Model Name** | `qwen3-embedding:0.6b` |
| **Model Family / Format** | `qwen3` / GGUF (Quantization: `Q8_0`) |
| **Parameter Count** | `595.78M` |
| **Model Disk Size** | `639 MB` (Storage Path: `E:\ollama\Models`) |
| **Context Window** | `32,768` tokens |
| **Embedding Dimension** | **1,024** |
| **Local Endpoint** | `http://localhost:11434` (Host) / `http://host.docker.internal:11434` (Docker Container) |
| **Docker Reachability** | **VERIFIED** (`http://host.docker.internal:11434` reachable inside `graphrag` container) |

---

## 2. 50-Chunk Performance Test Results (Task 2)

50 existing `DocumentChunk` texts were fetched from live TigerGraph database records containing valid Gemini embeddings and evaluated locally via Ollama.

### Empirical Latency & Throughput Metrics

| Metric | Value |
| :--- | :--- |
| **Total Chunks Evaluated** | 50 |
| **Total Elapsed Time** | **26.224 seconds** |
| **Cold Start Latency (Chunk 1)** | **18,291.08 ms** (~18.3s initial model GPU load) |
| **Warm Average Latency** | **160.37 ms / chunk** |
| **Overall Average Latency** | **522.99 ms / chunk** (including cold start) |
| **Warm Throughput** | **~6.23 chunks / second** |
| **Overall Throughput** | **1.91 chunks / second** |
| **Vector Dimension Verification** | **1024-dimensional** (50 / 50 vectors verified) |

### Warm Latency Trend Breakdown
- **Chunk 10**: 53.23 ms
- **Chunk 20**: 57.40 ms
- **Chunk 30**: 88.14 ms
- **Chunk 40**: 125.96 ms
- **Chunk 50**: 124.80 ms

### Hardware Evidence (GPU / VRAM / CPU)
- **GPU Hardware**: NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM)
- **Active Process**: `llama-server.exe` (PID 33532 running in CUDA Compute Mode)
- **VRAM Footprint**: ~3.3 GB VRAM utilized (~640 MB model weights + context buffer)

---

## 3. Query Embedding Test Results (Task 3)

5 representative public evaluation questions targeting distinct query categories were embedded locally via Ollama.

| Question Type | Sample Question Text | Latency (ms) | Dimension |
| :--- | :--- | :--- | :--- |
| **Lookup** (Cold reconnect) | *Which nations participated in Alpine Skiing Men's Downhill?* | 6,697.26 ms | 1024-d |
| **Temporal** | *Who won the gold medal in men's 20 kilometres walk immediately before 2016?* | 25.02 ms | 1024-d |
| **Multi-hop** | *Who won the gold medal in the event with the most competitors in sailing at the 2008 Summer Olympics?* | 27.01 ms | 1024-d |
| **Aggregation** | *How many events in biathlon at the 2018 Winter Olympics had more than 73 competitors?* | 23.75 ms | 1024-d |
| **Superlative** | *What sailing event at the 2008 Summer Olympics had the most competitors?* | 22.86 ms | 1024-d |

- **Total Query Latency**: `6.802 seconds`
- **Warm Average Query Latency**: **24.66 ms / query**
- **Query Vector Dimensions**: **1024-d** (5 / 5 questions verified)

---

## 4. Retrieval Compatibility Audit (Task 4)

1. **Which Python files need changes?**
   - `common/embeddings/embedding_services.py`: Add `Ollama_Embedding` service class implementing `embed_query` and `embed_documents`.
   - `common/config.py`: Add factory mapping for `embedding_model_service == "ollama"`.
   - `common/embeddings/tigergraph_embedding_store.py`: Pass 1024 dimension to TigerGraph schema initialization.

2. **Which configuration files need changes?**
   - `configs/local_server_config.json`:
     ```json
     "embedding_service": {
       "embedding_model_service": "ollama",
       "model_name": "qwen3-embedding:0.6b",
       "output_dimensionality": 1024,
       "ollama_url": "http://host.docker.internal:11434/api/embeddings"
     }
     ```

3. **Whether TigerGraph schema/index changes are required?**
   - **YES.** TigerGraph 4.2+ native vector attributes have fixed dimensionality (`embedding(dimension=1536)`). Storing 1024-d vectors requires running a GSQL schema change job to alter the attribute dimension or add a new vector attribute `qwen_embedding(dimension=1024, metric="cosine")` with an HNSW index.

4. **Whether existing 1536-d Gemini vectors can remain in the same attribute?**
   - **NO.** A single TigerGraph `VECTOR` attribute enforces strict fixed dimensionality. 1536-d and 1024-d vectors cannot co-exist in the same attribute.

5. **Whether all DocumentChunk embeddings must be replaced?**
   - **YES** (if replacing `embedding` in-place). Switching the primary graph attribute to 1024-d requires re-embedding all 5,716 `DocumentChunk` vertices using Qwen.

6. **Whether query embeddings and corpus embeddings must use the same Qwen model?**
   - **YES.** Cosine similarity math requires query and chunk vectors to inhabit the identical vector space generated by `qwen3-embedding:0.6b`.

7. **Whether the existing similarity/hybrid GSQL assumes 1536 dimensions?**
   - GSQL GDS functions dynamically accept vector arrays, but GSQL schema DDL (`SupportAI_Schema_Native_Vector.gsql`) explicitly defines `dimension=1536`.

8. **Whether a new vector attribute such as `qwen_embedding` would be safer than overwriting `embedding`?**
   - **YES, MUCH SAFER.** Adding `qwen_embedding(dimension=1024, metric="cosine")` preserves all 1,966 existing Gemini vectors intact without data loss, enabling zero-risk dual-model testing.

9. **Whether the existing GraphRAG retrieval path can use a 1024-d vector without architectural changes?**
   - **YES.** Python retrievers (`BaseRetriever`, `SimilarityRetriever`, `HybridRetriever`) handle vector arrays dynamically.

10. **Whether local Ollama API can be called from Docker container on Windows Docker Desktop?**
    - **YES, VERIFIED.** `http://host.docker.internal:11434/api/embeddings` was tested and confirmed 100% operational from inside the `graphrag` Docker container.

---

## 5. Estimated Full-Corpus Embedding Time (Task 5)

Using the empirical measurements from Task 2:

- **Corpus Size**: 5,716 `DocumentChunk` vertices
- **Warm Rate (~6.23 chunks/sec)**: **~15.3 minutes** (917.5 seconds)
- **Overall Rate (1.91 chunks/sec including cold start)**: **~50.0 minutes** (2,998 seconds)
- **Full Corpus + 100 Benchmark Queries**: **~15.7 minutes warm** / **~50.8 minutes overall**

*Note: These estimates are based on single-threaded HTTP requests without batching. Throughput can be further accelerated if Ollama request batching or parallel workers are used.*

---

## 6. Recommended Migration Strategy & Risk Assessment

### Recommended Safe Dual-Attribute Strategy
1. **Schema Extension**: Add a new vector attribute `qwen_embedding(dimension=1024, metric="cosine")` to `DocumentChunk` vertices via GSQL schema change.
2. **Parallel Ingestion**: Run a local Qwen embedding worker to populate `qwen_embedding` for all 5,716 chunks in ~15–30 minutes without touching existing `embedding` (Gemini 1536-d) vectors.
3. **Configuration Toggle**: Update `local_server_config.json` to point retrieval tools to `qwen_embedding`.

### Risk Assessment
- **Zero API Cost & Unlimited Quota**: 100% local execution eliminates API rate limits (HTTP 429) and quota windows.
- **Speed**: Full corpus embedding completes in ~15–30 minutes vs days waiting for API quota windows.
- **Risk**: Dual-attribute schema change requires TigerGraph GSQL schema change execution.

---

## 7. Mandatory Classification Section

### A. What Was Actually Tested
1. Local Ollama API responsiveness and model details for `qwen3-embedding:0.6b` (0.6B params, 1024-d).
2. End-to-end vector generation for 50 live TigerGraph `DocumentChunk` texts.
3. End-to-end query vector generation for 5 standard evaluation questions.
4. GPU acceleration status (`llama-server.exe` CUDA execution on RTX 3050 GPU).
5. Cross-environment connectivity from inside the `graphrag` Docker container to host Ollama (`http://host.docker.internal:11434`).
6. Vector dimension verification (100% returned 1024-d).

### B. What Was Inferred from Source-Code Inspection
1. TigerGraph 4.2+ native vector attribute DDL definition (`SupportAI_Schema_Native_Vector.gsql`).
2. Python embedding provider factory architecture (`common/embeddings/embedding_services.py`).
3. GSQL retrieval query vector array parameter dynamic passing.
4. Schema migration requirements for dual-vector attributes.

### C. What Remains Untested
1. Retrieval accuracy / recall quality of 1024-d Qwen vectors vs 1536-d Gemini vectors on the 100-question benchmark.
2. Full 5,716-chunk local embedding run end-to-end.
3. Parallel multi-threaded worker throughput to Ollama API.

---
**STOP.** Evaluation complete. No production vectors written. No graph mutation performed. No benchmark executed.
