# PHASE 14D-H — 20/20 OFFLINE ACCEPTANCE TEST REPORT

All 20 code-level acceptance tests were executed offline in the `graphrag` Docker container with 0 network calls.

## Test Execution Results Table

| Test ID | Description | Result | Details |
|---|---|---|---|
| **TEST 01** | Successful provider call | **PASS** | `http_attempts=1`, `retries=0` |
| **TEST 02** | Transient failure then success | **PASS** | `http_attempts=2`, `retries=1` |
| **TEST 03** | Transient failure twice | **PASS** | Failover triggered on 2nd failure |
| **TEST 04** | HTTP 402 Payment Required | **PASS** | `http_attempts=1`, `retries=0`, circuit broken |
| **TEST 05** | Daily quota permanent 429 | **PASS** | `http_attempts=1`, `retries=0`, circuit broken |
| **TEST 06** | Transient 429 (Retry-After <= 30s) | **PASS** | Max 2 HTTP attempts |
| **TEST 07** | HTTP 5xx Server Error | **PASS** | Max 2 HTTP attempts |
| **TEST 08** | Connection timeout | **PASS** | Max 2 HTTP attempts |
| **TEST 09** | Parser failure | **PASS** | Operates locally, 0 extra provider retries |
| **TEST 10** | ChatOpenAI max_retries == 0 | **PASS** | Configured in `airouter_llm_service.py` |
| **TEST 11** | BudgetTracker accounting | **PASS** | `logical_llm_calls=1`, `http_attempts=2` |
| **TEST 12** | Budget exhausted | **PASS** | 0 attempts executed when budget cap reached |
| **TEST 13** | MAX_REPLANS = 0 | **PASS** | Zero recovery replans |
| **TEST 14** | MAX_REPLANS = 1 | **PASS** | Maximum one recovery replan |
| **TEST 15** | MAX_REPLANS = 3 | **PASS** | Maximum three recovery replans |
| **TEST 16** | Multi-hop 1st insufficient result | **PASS** | Exactly 1 recovery replan permitted |
| **TEST 17** | Multi-hop 2nd insufficient result | **PASS** | 0 additional replans permitted |
| **TEST 18** | Successful sufficient retrieval | **PASS** | 0 replans permitted (`has_context == True`) |
| **TEST 19** | Planner failure fallback | **PASS** | Keyword-based fallback without recursive LLM call |
| **TEST 20** | Provider retry call count | **PASS** | Retry does NOT increment `logical_llm_calls` |

---
**SUMMARY**: **20/20 ACCEPTANCE TESTS PASSED (100%)**
