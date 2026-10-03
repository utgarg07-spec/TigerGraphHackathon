# PHASE 13 — GATE 5 REGRESSION REPORT

## 1. Executive Summary
- **Phase 6 Deterministic Tool Suite**: **78 / 78 PASS (100%)**
- **Targeted Regression Suite**: **9 / 9 SUCCESS (100% HTTP Success, 0 Timeouts)**
- **Primary Operational Breakthrough**: Questions `pub-023`, `pub-060`, and `pub-098` (which previously suffered from ~180s HTTP timeouts under FreeLLMAPI during Phase 12) executed cleanly under Groq provider routing with zero timeouts and latencies between 56.7s and 112.3s.

---

## 2. Phase 6 Deterministic Tools Test Suite
- **Command**: `pytest tests/test_phase6_tools.py`
- **Result**: **78 passed in 0.42s**
- **Status**: **PASS (78/78)**

---

## 3. Targeted Regression Cases (9 QIDs)

| QID | QType | Result | Latency (s) | Steps | Key Findings / Status |
|---|---|---|---|---|---|
| `pub-004` | superlative | `SUCCESS` | 47.69s | 9 | Factual baseline intact |
| `pub-008` | superlative | `SUCCESS` | 105.49s | 9 | Multi-step superlative search completed without timeout |
| `pub-015` | multi_hop | `SUCCESS` | 70.78s | 3 | Output formatted as expected |
| `pub-023` | multi_hop | `SUCCESS` | 67.82s | 3 | **RESOLVED TIMEOUT**: Completed in 67.8s (was 180s timeout in Phase 12) |
| `pub-060` | multi_hop | `SUCCESS` | 56.72s | 3 | **RESOLVED TIMEOUT**: Completed in 56.7s (was 180s timeout in Phase 12) |
| `pub-067` | multi_hop | `SUCCESS` | 70.49s | 3 | Exact match produced ("Rosannagh MacLennan") |
| `pub-076` | multi_hop | `SUCCESS` | 75.91s | 3 | Exact match produced ("Julia Mancuso") |
| `pub-098` | multi_hop | `SUCCESS` | 112.31s | 3 | **RESOLVED TIMEOUT**: Completed in 112.3s (was 180s timeout in Phase 12) |
| `pub-099` | multi_hop | `SUCCESS` | 27.89s | 3 | Fast synthesis completed |

---

## 4. Operational & Timeout Impact
- **Phase 12 Historical Baseline**: Questions `pub-023`, `pub-060`, `pub-098` hit the 180s client timeout boundary.
- **Phase 13 Post-Fix Verification**: Under Groq `qwen/qwen3.8-27b`, all 9 targeted cases finished within the 180s boundary. Zero timeouts occurred.

---

## 5. Gate 5 Final Status
- **Status**: **PASS**
- **Decision**: Proceed to **Gate 6 — 5-Question End-to-End Agentic Smoke Test**.
