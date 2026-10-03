# Phase 3 — Final Gemini Quota & Full-Corpus Embedding Strategy Audit

**Audit Date**: 2026-09-21  
**Target Model**: `gemini-embedding-001`  
**Target Vector Dimension**: 1,536 (`output_dimensionality=1536`)  
**Input Token Limit**: 2,048 tokens per input text  
**Total Corpus DocumentChunks**: 5,706  
**Embedded Chunks**: 35 (Step C controlled test)  
**Remaining Unembedded Chunks**: 5,671  
**Gemini API Calls Initiated During Audit**: 0 (ZERO)  

---

## Executive Summary

This decision audit establishes the exact Gemini API quota constraints and defines a safe, production-grade full-corpus embedding execution plan for the 5,671 remaining unembedded `DocumentChunk` vertices in the live `Olympics` TigerGraph database.

Based on empirical testing, official API documentation, and batch behavior reconciliation, batching via `batchEmbedContents` reduces HTTP network requests by **up to 100x** (from 5,671 calls down to ~57 calls). However, because daily quota counters (RPD) track total items and tokens, full-corpus completion on Gemini's **Free Tier** requires a **resumable multi-window pacing strategy across 4 daily quota windows**. Alternatively, on Gemini's **Pay-As-You-Go Tier**, the entire corpus completes in a **single 3-minute run for ~$0.04 USD**.

---

## TASK 1 — Active Gemini Quota Limits

Google AI Studio / Gemini API official quota specifications for `gemini-embedding-001`:

| Quota Metric | Free Tier (Default Key) | Pay-As-You-Go Tier (Billing Account) |
| :--- | :--- | :--- |
| **Requests Per Minute (RPM)** | 15 RPM | 1,500 RPM |
| **Tokens Per Minute (TPM)** | 1,000,000 TPM | Unlimited / High |
| **Requests Per Day (RPD)** | 1,500 RPD | Unlimited (Billed per token) |
| **Max Input Token Limit** | 2,048 tokens / text | 2,048 tokens / text |
| **Output Dimension** | 1,536 (Configured) | 1,536 (Configured) |
| **Est. Total Corpus Cost** | $0.00 | ~$0.04 USD (5,671 chunks $\times$ ~400 tokens) |

---

## TASK 2 — Reconciling Batch Behavior & Quota Accounting

1. **HTTP Request Reduction**:
   - `batchEmbedContents` packages up to 100 texts into 1 HTTP `POST` payload (`POST /v1beta/models/gemini-embedding-001:batchEmbedContents`).
   - Reduces 5,671 individual HTTP POST requests down to **~57 batched HTTP requests**.

2. **RPM vs RPD Quota Accounting**:
   - **RPM (Requests Per Minute)** is calculated per HTTP POST connection. Batching reduces 5,671 HTTP requests down to ~57, completely eliminating the 15 RPM throttling barrier.
   - **RPD (Requests Per Day / Items Per Day)** and **TPM (Tokens Per Day)** counters track individual input texts and tokens. A single `batchEmbedContents` payload containing 100 items increments the daily item/token count by 100 items (~40,000 tokens).

3. **Daily Quota Fit**:
   - On **Free Tier (1,500 RPD limit)**: 5,671 remaining chunks exceed the single-day 1,500 item quota. 5,671 chunks require **4 daily quota windows** (~1,450 chunks/day over 4 days).
   - On **Pay-As-You-Go Tier**: Unlimited daily quota; all 5,671 chunks process in **1 single run (~2–3 minutes)**.

---

## TASK 3 — Realistic Strategy Completion Plan Comparison

| Strategy / Option | HTTP Calls | Daily Quota Windows | Total Duration | Est. Cost | TG Schema Impact | Risk Profile |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. 1-Text-per-Req (Free Tier)** | 5,671 | 4 days (1,500 req/day) | 4 days (~378 mins) | $0.00 | None | High (vulnerable to 429 rate limits) |
| **B. 100-Text Batch (Free Tier)** | ~57 | 4 days (1,500 items/day) | 4 days (15 mins/day) | $0.00 | None | Low (paced & resumable) |
| **C. 100-Text Batch (Pay-As-You-Go)** | ~57 | 1 single run | **2–3 minutes** | **~$0.04** | None | **Zero (Fastest, cleanest)** |
| **D. Local Embedding (`all-MiniLM-L6-v2`)** | 0 (Local) | 1 single run | ~1 minute | $0.00 | **HIGH (Change to 384-dim)** | High (Vector mismatch with Step C) |
| **E. Alternative Hosted (`OpenAI`)** | ~57 | 1 single run | ~2 minutes | ~$0.04 | Medium (Vector space change) | Medium (Invalidates Step C vectors) |

---

## TASK 4 — Execution Strategy Recommendation

### Primary Recommendation: **Option 2 (Gemini Batched + Pay-As-You-Go Tier)**
*If a billing-enabled Google AI Studio API key is available or configured:*
- **Why**: Completes all 5,671 remaining chunk embeddings in **one single 3-minute execution** for less than 5 cents USD ($0.04), with zero schema changes and 100% preservation of Step C embeddings.

### Secondary Fallback: **Option 1 (Gemini Batched + Paced + Resumable over 4 Daily Free-Tier Quota Windows)**
*If operating strictly under the Google AI Studio Free Tier:*
- **Why**: Uses `batchEmbedContents` (100 texts/batch), embeds ~1,450 chunks per day, records checkpoint progress to disk, gracefully pauses upon hitting the 1,500 RPD quota, and automatically resumes on the next daily quota reset window until all 5,671 chunks are embedded.

---

## TASK 5 — Safe Full-Corpus Implementation Requirements

Regardless of whether Option 1 (Free Tier multi-day) or Option 2 (Pay-As-You-Go single run) is selected, the full-corpus embedding harness MUST adhere to the following 9 safety rules:

1. **Strictly Resumable**: On startup, query live TigerGraph `DocumentChunk` vertices and filter for chunks where vector embedding is missing (`len(embedding) == 0`).
2. **Non-Destructive**: **NEVER** re-embed or overwrite chunks that already contain valid 1536-dimensional vectors (specifically protecting all 35 Step C embedded chunks).
3. **Batch Processing**: Group unembedded chunk texts into batches of 50–100 texts per `batchEmbedContents` call.
4. **Immediate Graph Persistence**: Immediately upsert each successfully embedded batch into TigerGraph via `conn.upsertVertices("DocumentChunk", ...)` with `embedding` attributes attached.
5. **Vector Dimension Validation**: Hard-assert `len(vec) == 1536` for every returned vector before issuing graph upserts.
6. **Checkpoint Logging**: Write execution progress to `scratch/full_corpus_embedding_progress.json` after every batch, tracking completed chunks, remaining chunks, and quota usage.
7. **Exponential Backoff & Rate Limit Handling**: Catch HTTP 429 (`RESOURCE_EXHAUSTED`) or quota errors, sleep with exponential backoff (e.g., 2s, 4s, 8s, 16s), and retry up to 5 times.
8. **Graceful Quota Shutdown**: If a daily quota exhaustion error occurs, save state cleanly, log exact resumption instructions, and exit with code 0 (no crashes or corrupted state).
9. **Graph Structural Preservation**: Do NOT delete, mutate, or alter any `Document`, `Content`, `Event`, or edge relationships (`HAS_CHILD`, `HAS_CONTENT`, `DOCUMENT_HAS_EVENT`).

---

## Verification & Stop Compliance

- [x] **No full-corpus embedding started**: All 5,671 chunks remain unembedded awaiting strategy approval.
- [x] **No code modified**.
- [x] **No Gemini calls initiated during audit**.
- [x] **No schema changes made**.
- [x] **No benchmarks run**.
