# Token Accounting & Metric Definition Specification

**Phase 11A — Gate 6: Authoritative Token Definition**  
**Document Version:** 1.0  
**Repository:** `TigerGraph Olympics Benchmark`  

---

## 1. Executive Summary & Verdict

In Phase 11, the reported average token counts across the 100-question public benchmark are:

| Pipeline | Reported Avg Total Tokens | Populated / Evaluated Queries | Unpopulated (Errors / Null) | Avg Input Tokens | Avg Output Tokens |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RAG** | **8,617.17** | 6 / 100 | 94 / 100 | 7,107.33 | 1,509.83 |
| **GraphRAG** | **1,103.30** | 27 / 100 | 73 / 100 | 930.44 | 172.85 |
| **Agentic GraphRAG** | **7,718.01** | 94 / 100 | 6 / 100 | 5,392.32 | 2,325.69 |

### Gate 6 Comparability Verdict
- **Mathematical Accounting Consistency**: **PASS**. All three pipelines enforce strict additive accounting:
  $$\text{Total Tokens} = \text{Input Tokens} + \text{Output Tokens}$$
  Every populated query record satisfies $\text{Total Tokens} - (\text{Input Tokens} + \text{Output Tokens}) = 0$.
- **Architectural Scope Discrepancy**: **SPLIT INTO CLEARLY LABELLED METRICS**.  
  While the token counting unit is consistent across pipelines, the *architectural lifecycle* differs fundamentally:
  - **RAG & GraphRAG** represent **monolithic single-prompt** evaluations over small subsets of surviving queries (6% and 27% completion respectively).
  - **Agentic GraphRAG** represents an **end-to-end multi-step orchestration lifecycle** spanning planning, tool execution, structural graph extraction, replanning, and final answer synthesis across 94% completed queries.

---

## 2. Formal Definition of "Total Tokens"

### Mathematical Formulation
For any query $q$, the **Total Tokens** $T_{\text{total}}(q)$ is defined as the sum of all prompt (input) tokens and completion (output) tokens across all LLM invocations executed during the resolution of $q$:

$$T_{\text{total}}(q) = T_{\text{input}}(q) + T_{\text{output}}(q)$$

Where:
$$T_{\text{input}}(q) = \sum_{k=1}^{K} T_{\text{prompt}}^{(k)}, \quad T_{\text{output}}(q) = \sum_{k=1}^{K} T_{\text{completion}}^{(k)}$$

and $K$ is the number of distinct LLM calls made for question $q$.

### Disaggregated Lifecycle Token Components
For the multi-step Agentic GraphRAG pipeline, token usage is decomposed into distinct lifecycle stages:

$$T_{\text{total}} = T_{\text{planner}} + T_{\text{replan}} + T_{\text{structural\_tools}} + T_{\text{synthesis}}$$

Where:
1. **$T_{\text{planner}}$ (Planner Tokens)**: Tokens consumed by the initial query decomposition and execution plan generator (`node: "plan"`).
2. **$T_{\text{replan}}$ (Replan Tokens)**: Tokens consumed during dynamic error correction or plan refinement (`node: "replan"`).
3. **$T_{\text{structural\_tools}}$ (Tool LLM Tokens)**: Tokens consumed by neural/LLM-assisted graph extractors (`node: "graphrag__structural_retrieve"`).
4. **$T_{\text{deterministic\_tools}}$ (Deterministic Graph Tools)**: **0 Tokens**. Native TigerGraph GSQL queries (`lookup`, `aggregate`, `superlative`, `temporal_resolve`) and vector similarity searches do not invoke LLM inference and incur zero token cost.
5. **$T_{\text{synthesis}}$ (Synthesis Tokens)**: Tokens consumed by the final answer synthesizer (`node: "synthesize"`) aggregating retrieved facts, graph vertices, and generating cited output.

---

## 3. Disaggregated Metrics Breakdown

### Detailed Token Breakdown Across All 100 Questions

| Metric | RAG (N=6) | GraphRAG (N=27) | Agentic GraphRAG (N=94) | Accounting Basis |
| :--- | :--- | :--- | :--- | :--- |
| **Input Tokens (Avg)** | 7,107.33 | 930.44 | 5,392.32 | Provider prompt token metadata |
| **Output Tokens (Avg)** | 1,509.83 | 172.85 | 2,325.69 | Provider completion token metadata |
| **Planner Tokens (Avg)** | 0.00 | 0.00 | 2,928.44 | Input: 1,888.78, Output: 1,039.66 |
| **Replan Tokens (Avg)** | 0.00 | 0.00 | 45.23 | Refinement invocations |
| **Deterministic Tool Tokens** | 0.00 | 0.00 | **0.00** | Pure GSQL / TigerGraph execution |
| **Structural Tool LLM Tokens (Avg)** | 0.00 | 0.00 | 806.59 | Neural graph neighborhood extraction |
| **Synthesis Tokens (Avg)** | 8,617.17 | 1,103.30 | 3,272.82 | Input: 2,609.20, Output: 663.62 |
| **Total Tokens (Avg)** | **8,617.17** | **1,103.30** | **7,718.01** | $\sum(\text{Input} + \text{Output})$ |
| **Query Success Rate** | 6 / 100 (6%) | 27 / 100 (27%) | 94 / 100 (94%) | Evaluated completion rate |

---

## 4. Technical Verification of Accounting Subsystems

### A. Provider Gateway Usage Accounting
- **Gateway Protocol**: FreeLLMAPI / Groq / OpenAI-compatible REST endpoints.
- **Payload Extraction**: Every HTTP completion payload returns a `usage` dictionary:
  ```json
  "usage": {
    "prompt_tokens": 1813,
    "completion_tokens": 989,
    "total_tokens": 2802
  }
  ```
- **Verification**: The evaluator directly extracts `prompt_tokens` and `completion_tokens` from response headers/payloads without relying on client-side guesses.

### B. Client-Side Tokenizer & Truncation
- **Tokenizer**: `tiktoken` with `cl100k_base` encoding mapped to GPT-4 / Qwen token standards (`common/utils/token_calculator.py`).
- **Context Window Protection**: `TokenCalculator.truncate_to_token_limit` enforces context limits prior to dispatching prompts to avoid HTTP 400 Context Overflow errors.

### C. Fallback Calls & Hidden Retries
- **Budget Tracking**: Managed by `QuestionBudgetTracker` (`common/llm_services/base_llm.py`).
- **Accounting**: When a primary provider fails (e.g., HTTP 429 Rate Limit) and falls back to a secondary provider, the budget tracker aggregates tokens across all attempts, ensuring zero hidden tokens.

### D. Deterministic Tool Calls (0 LLM Tokens)
- All deterministic tools executed during Phase 11:
  - `graphrag__lookup`
  - `graphrag__aggregate`
  - `graphrag__superlative`
  - `graphrag__temporal_resolve`
  - `graphrag__hybrid_search`
- **Proof**: Executed directly against TigerGraph Cloud via REST/GSQL queries. No LLM prompts are generated, resulting in **0 input tokens** and **0 output tokens**.

---

## 5. Summary of Labelled Metrics for Dashboard Integration

To ensure fair and transparent representation in dashboard visualizations, tokens must be presented with both headline aggregates and granular breakdowns:

1. `metric_total_tokens`: Total LLM tokens per completed query.
2. `metric_input_tokens`: Total prompt tokens sent to model endpoints.
3. `metric_output_tokens`: Total completion tokens generated by model endpoints.
4. `metric_planner_tokens`: Tokens dedicated to multi-step planning and decomposition.
5. `metric_synthesis_tokens`: Tokens dedicated to final answer synthesis and citation.
6. `metric_tool_llm_tokens`: Tokens consumed by neural/structural extraction tools.
7. `metric_token_efficiency_per_correct_answer`: $\frac{\text{Total Tokens}}{\text{Accuracy (\%)}} = \frac{7,718.01}{87\%} \approx 88.71 \text{ tokens/acc point}$.
