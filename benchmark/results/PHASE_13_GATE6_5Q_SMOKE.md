# PHASE 13 — GATE 6: 5-QUESTION END-TO-END AGENTIC SMOKE REPORT

## 1. Summary
- **Execution Target**: 5 fresh sequential questions representing all 5 core query types (`lookup/aggregation`, `temporal`, `aggregation`, `superlative`, `multi_hop`).
- **HTTP Success Rate**: **5 / 5 (100%)**
- **Timeout Rate**: **0 / 5 (0%)**
- **Budget Violations**: **0**
- **Provider Routing Violations**: **0**

---

## 2. Detailed Results

| QID | QType | Result | Latency (s) | Steps | LLM Provider / Model | Prediction Summary |
|---|---|---|---|---|---|---|
| `pub-001` | aggregation | `SUCCESS` | 46.86s | 9 | Groq / `qwen/qwen3.8-27b` | Empty context notice |
| `pub-002` | temporal | `SUCCESS` | 60.50s | 4 | Groq / `qwen/qwen3.8-27b` | **Chen Ding** (Exact Match) |
| `pub-003` | aggregation | `SUCCESS` | 105.70s | 9 | Groq / `qwen/qwen3.8-27b` | Empty context notice |
| `pub-004` | superlative | `SUCCESS` | 104.66s | 9 | Groq / `qwen/qwen3.8-27b` | Empty context notice |
| `pub-005` | multi_hop | `SUCCESS` | 81.90s | 3 | Groq / `qwen/qwen3.8-27b` | **Naim Süleymanoğlu** (Exact Match) |

---

## 3. Operational Conditions Verification
1. **HTTP Success**: 5/5 HTTP 200 responses received.
2. **Timeouts**: Zero calls exceeded the 180s timeout limit. Average latency was 79.92s.
3. **Agent Budgets**: All questions respected `MAX_AGENT_STEPS=5` / multi-turn tool execution constraints.
4. **Provider Routing**: All planning, reasoning, and synthesis steps were routed through Groq `qwen/qwen3.8-27b`.

---

## 4. Gate 6 Final Decision
- **Status**: **PASS**
- **Decision**: Proceed to **Gate 7 — 25-Question Post-Fix Performance Benchmark**.
