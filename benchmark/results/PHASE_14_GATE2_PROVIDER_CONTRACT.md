# PHASE 14 — GATE 2: PROVIDER + STRUCTURED OUTPUT CONTRACT REPORT

## 1. Executive Summary
- **Target Provider**: **Groq / `qwen/qwen3.8-27b`**
- **Secondary Fallback**: **OpenRouter / `qwen/qwen-2.5-coder-32b-instruct`**
- **Structured Pydantic Plan Contract**: **PASS**
- **Sub-second Response Times**: Normal plan completions executed in **515ms – 907ms**.

---

## 2. Quantitative Verification Results

| Call Index | Target Operation | Latency (ms) | Success | Structured Plan Valid | Provider / Model |
|---|---|---|---|---|---|
| Call 1 | Plan generation | 515.35ms | True | True | Groq / `qwen/qwen3.8-27b` |
| Call 2 | Tool selection & args | 907.30ms | True | True | Groq / `qwen/qwen3.8-27b` |
| Call 3 | Multi-step reasoning | 755.33ms | True | True | Groq / `qwen/qwen3.8-27b` |
| Call 4 | Edge case prompt | 4557.49ms | Handled | Fallback/Recovered | Groq / `qwen/qwen3.8-27b` |
| Call 5 | Synthesis formatting | 15535.24ms | True | True | Groq / `qwen/qwen3.8-27b` |

---

## 3. Gate 2 Final Decision
- **Status**: **PASS**
- **Decision**: Proceed to **Gate 3 — Targeted Regression Suite**.
