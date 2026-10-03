# PHASE 14 — GATE 0: PRE-FLIGHT + IMMUTABILITY AUDIT REPORT

## 1. Executive Summary
- **Status**: **PASS**
- **Phase 12 Historical Baseline**: Fully verified and frozen. SHA-256 fingerprints recorded for all authoritative artifacts.
- **Phase 13 Routing State**: Active and operational.
  - `planning` $\rightarrow$ **Groq / `qwen/qwen3.8-27b`**
  - `reasoning` $\rightarrow$ **Groq / `qwen/qwen3.8-27b`**
  - `synthesis` $\rightarrow$ **Groq / `qwen/qwen3.8-27b`**
  - `synthesis fallback` $\rightarrow$ **OpenRouter / `qwen/qwen-2.5-coder-32b-instruct`**
- **Budgets & Boundaries**:
  - `MAX_AGENT_STEPS = 5`
  - `MAX_LLM_CALLS = 6`
  - `MAX_PLAN_RETRIES = 2`
  - Client timeout boundary = `180s`

---

## 2. Protected Artifact Fingerprints

| Artifact Path | SHA-256 Checksum | Immutability Status |
|---|---|---|
| `benchmark/results/FINAL_AGENTIC_100_LIVE.jsonl` | `996b0ae5cc5ebae8963a9d065df6e5bd3cc4e9d0d9c8119e0c1386dc6e95b835` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_AGENTIC_100_SUMMARY.json` | `eb363e37f460f2646084e558af792a0ee3755f66fb939da33e057e5fd5384fa0` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_AGENTIC_100_REPORT.md` | `2804f68ebb1904b5ef9ba0e1dcc87a22bada9b678623ecff40962fdd13f60915` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_AGENTIC_100_QID_TRACE.csv` | `87acb0bf3a10bed9fcf7e4c4f6b1a8b590dd51fcb8463bf0f1c615b6c9b5e204` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_THREE_WAY_100.jsonl` | `1179c82c39d85b2a8083a7e10b551813328ae45ef9f33d2f1ff1012fe48ed853` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_THREE_WAY_SUMMARY.json` | `e5680b91d93424c1585e6631ffc7e20bbde0ca78458e9f4ad78cadf1404db479` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_THREE_WAY_COMPARISON.csv` | `383c6c79429677d790ebb5d7f3c385c044c56e4b75333fc5a7ad54691d084351` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_THREE_WAY_QTYPE.csv` | `49310a368e838cf750eca3fb59e1f0b9ae4bd1314a56db87c1c61ad7e820699d` | **FROZEN / UNMODIFIED** |
| `benchmark/results/FINAL_AGENTIC_EFFECTIVENESS.json` | `d0d536472ee4a63ea39a87968441f01dd690ea1b2990b1d4466cff9840973756` | **FROZEN / UNMODIFIED** |
| `benchmark/results/PHASE_13_FINAL_SUMMARY.json` | `42ea41c8c5dc293ccf930584810bd3a65528891a5fe1b524202979abe90af320` | **FROZEN / UNMODIFIED** |
| `benchmark/results/PHASE_13_FINAL_REPORT.md` | `f1bb0c628bfc18c7f6d2ef399c279af998c0e2ee162fac729c65dd377db8fc69` | **FROZEN / UNMODIFIED** |

---

## 3. Gate 0 Final Decision
- **Status**: **PASS**
- **Decision**: Proceed to **Gate 1 — Phase 6 Core Regression**.
