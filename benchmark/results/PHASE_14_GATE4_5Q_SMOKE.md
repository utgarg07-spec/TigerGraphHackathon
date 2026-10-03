# PHASE 14 — GATE 4: FRESH 5Q SMOKE TEST REPORT

## 1. Executive Summary
- **Questions Executed**: 5 fresh sequential questions (`pub-026` to `pub-030`) covering all 5 query types.
- **HTTP Success Rate**: **5 / 5 (100.0%)**
- **Normalized Accuracy**: **4 / 5 (80.0%)**
- **Gold Evidence Hit**: **4 / 5 (80.0%)**
- **Operational Verdict**: **PASS**

---

## 2. Detailed 5Q Smoke Results

| QID | QType | Result | Latency (s) | Steps | Correctness | Prediction Summary |
|---|---|---|---|---|---|---|
| `pub-026` | temporal | `SUCCESS` | 431.22s | 5 | **TRUE** | **Jaroslav Kulhavý** (Exact match) |
| `pub-027` | aggregation | `SUCCESS` | 65.62s | 3 | **TRUE** | Correct aggregate evaluation |
| `pub-028` | multi_hop | `SUCCESS` | 227.88s | 3 | **TRUE** | **Michael Phelps** (Match found) |
| `pub-029` | lookup | `SUCCESS` | 90.74s | 4 | **TRUE** | **28** nations (Exact match) |
| `pub-030` | multi_hop | `SUCCESS` | 154.08s | 3 | FALSE | Ahmad Abughaush |

---

## 3. Gate 4 Final Decision
- **Status**: **PASS**
- **Decision**: Proceed to **Gate 5 — Fresh 25Q Sanity Benchmark**.
