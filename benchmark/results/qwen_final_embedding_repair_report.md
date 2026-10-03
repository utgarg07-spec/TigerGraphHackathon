# Phase 3 — Final Qwen Embedding Repair Report

## Executive Summary

The Phase 3 full-corpus Qwen embedding repair has **PASSED 100%**. All 43 missing `DocumentChunk` vertices previously affected by the captive-portal HTTP interception window have been successfully embedded and persisted in TigerGraph using the local `qwen3-embedding:0.6b` model.

**100% of the 5,716 DocumentChunk vertices now contain valid 1024-dimensional Qwen embeddings.**

---

## 1. Live Authoritative TigerGraph Graph Audit

| Metric | Pre-Repair State | Post-Repair Final State | Validation Target | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Total `DocumentChunk` Vertices** | 5,716 | **5,716** | 5,716 | **PASSED** |
| **`qwen_embedding` Present (1024-d)** | 5,673 | **5,716** | 5,716 | **PASSED (100%)** |
| **`qwen_embedding` Missing** | 43 | **0** | 0 | **PASSED** |
| **Gemini `embedding` (1536-d)** | 1,966 | **1,966** | 1,966 | **PASSED (100% Preserved)** |
| **Total `Event` Vertices** | 2,162 | **2,162** | 2,162 | **PASSED** |
| **`DOCUMENT_HAS_EVENT` Edges** | 2,162 | **2,162** | 2,162 | **PASSED** |
| **Duplicate Chunk IDs** | 0 | **0** | 0 | **PASSED** |
| **Schema Mutations** | None | **None** | None | **PASSED** |

---

## 2. Repaired Chunk Details

The repair script targeted exactly the 43 failed chunk IDs:

`Q1005192_chunk_0`, `Q1005557_chunk_0`, `Q1005811_chunk_1`, `Q10572431_chunk_0`, `Q107861723_chunk_1`, `Q1095367_chunk_1`, `Q1156252_chunk_5`, `Q1222641_chunk_0`, `Q1222651_chunk_0`, `Q12808128_chunk_0`, `Q1360804_chunk_2`, `Q1408881_chunk_0`, `Q17515790_chunk_0`, `Q2000988_chunk_2`, `Q2070832_chunk_0`, `Q22964444_chunk_2`, `Q2463752_chunk_4`, `Q24761058_chunk_0`, `Q2500292_chunk_0`, `Q25991452_chunk_1`, `Q26228283_chunk_0`, `Q26234144_chunk_1`, `Q26860_chunk_1`, `Q280553_chunk_0`, `Q30680433_chunk_0`, `Q3499066_chunk_1`, `Q3628683_chunk_5`, `Q3628777_chunk_2`, `Q3998590_chunk_1`, `Q47155555_chunk_1`, `Q47295256_chunk_1`, `Q4903025_chunk_7`, `Q599322_chunk_1`, `Q645932_chunk_2`, `Q65242164_chunk_3`, `Q65242174_chunk_2`, `Q677063_chunk_1`, `Q735286_chunk_2`, `Q7979972_chunk_0`, `Q7979977_chunk_1`, `Q843436_chunk_6`, `Q914969_chunk_0`, `Q937526_chunk_0`

---

## 3. Repair Execution & Performance Summary

- **Total Repaired Chunks**: 43
- **Repair Elapsed Time**: 31.41 seconds
- **Throughput**: 1.37 chunks / second
- **Ollama API Requests**: 43 HTTP requests to `http://host.docker.internal:11434/api/embeddings`
- **Embedding Failures / Retries**: 0
- **Network Health**: TigerGraph REST endpoint (`http://localhost:9000`) and Ollama local endpoint returned valid HTTP 200 JSON responses without captive-portal interception.

---

## 4. Verification & Safeguards Compliance

1. **Zero Overwriting of Gemini Vectors**: All 1,966 original Gemini 1536-d vectors remain completely untouched and valid.
2. **Dimension Integrity**: All 5,716 `qwen_embedding` vectors have dimension = 1024.
3. **No Schema Changes**: Graph schema (version 6) was preserved with no DDL modifications.
4. **Deterministic Olympic Structures**: All 2,162 `Event` vertices and 2,162 `DOCUMENT_HAS_EVENT` edges remain 100% verified.
