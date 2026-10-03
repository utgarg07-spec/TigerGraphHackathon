# PHASE 14D-I — ONE CONTROLLED LIVE VALIDATION REPORT

**PHASE 14D-I STATUS**: `FAIL`

| Parameter | Value |
|---|---|
| **QUESTION** | `pub-004` |
| **HTTP STATUS** | `SUCCESS` |
| **TOTAL LATENCY** | `10.098s` |
| **PLANNER** | `PASS` |
| **EXPECTED TOOL** | `graphrag__superlative` |
| **ACTUAL TOOL** | `graphrag__superlative` |
| **RETRIEVAL** | `FAIL` |
| **REPLAN COUNT** | `0` |
| **LOGICAL LLM CALLS** | `3` |
| **PROVIDER HTTP ATTEMPTS** | `3` |
| **PROVIDER RETRIES** | `0` |
| **PROVIDER FAILOVERS** | `0` |
| **AGENT STEPS** | `1` |
| **SYNTHESIS** | `PASS` |
| **RETRY INVARIANTS** | `PASS` |
| **BUDGET INVARIANTS** | `PASS` |
| **PHASE 12 MODIFIED** | `NO` |
| **PHASE 13 MODIFIED** | `NO` |
| **API QUESTIONS EXECUTED** | `1` |
| **NEXT GATE** | `STOP` |

## Tool Arguments
```json
{
  "sport": "athletics",
  "games": "2008 Summer Olympics"
}
```

## Final Answer
> According to the provided corpus, the athletics event at the 2008 Summer Olympics with the highest number of competitors was **Athletics at the 2008 Summer Olympics – Men's marathon**, which had 95 competitors.

## Gate Verification Breakdown
- `pub_004_completed_http_success`: **PASS**
- `no_http_timeout`: **PASS**
- `planner_completed`: **PASS**
- `expected_tool_superlative`: **PASS**
- `tool_arguments_valid`: **PASS**
- `deterministic_tool_executed`: **PASS**
- `evidence_context_returned`: **FAIL**
- `no_uncontrolled_retry`: **PASS**
- `provider_attempts_lte_2`: **PASS**
- `logical_calls_lte_6`: **PASS**
- `agent_steps_lte_5`: **PASS**
- `replans_lte_1`: **PASS**
- `synthesis_completed`: **PASS**
- `final_answer_not_fallback`: **PASS**
- `telemetry_fields_consistent`: **PASS**
- `no_phase12_13_artifact_changed`: **PASS**
- `exactly_one_question_executed`: **PASS**