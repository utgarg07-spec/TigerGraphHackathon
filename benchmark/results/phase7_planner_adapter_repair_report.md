# Phase 7A Planner Adapter Repair Report

## A. Failure Reproduction

During the initial 100-question Phase 7 standard agentic benchmark (`mode=agentic`, `agent_style=planned`, `pass_qtype=False`), all 100 HTTP requests completed with a 0% zero-context rate and 74/100 gold-document recall. However, inspection revealed that the planner called `graphrag__hybrid_search` for all 100 questions, and the four Phase 6 deterministic Olympic tools were invoked 0 times.

### Code Path of Failure

```text
LLM response (Groq openai/gpt-oss-20b)
    ↓
Groq API 400 Bad Request ("attempted to call tool 'json' which was not in request.tools")
    ↓
LangChain with_structured_output(Plan) raises exception
    ↓
base_llm.invoke_structured exception handler (missing failed_generation adapter & missing field mapping)
    ↓
agentic_planner catch block
    ↓
fallback to single hybrid step
    ↓
graphrag__hybrid_search (100% of benchmark queries)
```

---

## B. Existing Plan Contract

The Plan schema contract was inspected in `common/py_schemas/schemas.py`:

* **Plan Schema**: `Plan`
  * `steps: List[PlanStep] = []`
  * `strategy: str = ""`
* **Step Schema**: `PlanStep`
  * `id: str` (Step ID)
  * `kind: str = "unstructured"` (Step classification)
  * `tool: str` (Name of registered tool to execute)
  * `args: Dict = {}` (Tool keyword arguments)
  * `arg_bindings: Dict[str, str] = {}` (Inter-step dependencies)
  * `depends_on: List[str] = []` (Dependency step IDs)
  * `rationale: str = ""` (Step description)
* **Planner Return Type**: `Plan` Pydantic model instance.
* **Executor Expected Input**: `(plan: Plan, ctx)` where `ctx` provides graph connection (`conn`), query context, and trace logging (`emit`).
* **Tool Catalog**: Passed via `catalog()` from `tools.tool_registry`, containing 12 tools (4 Phase 6 deterministic Olympic tools + 8 standard tools).

---

## C. Root Cause

1. **Groq Function-Call Envelope**: The Groq completion model `openai/gpt-oss-20b` returns structured tool calls wrapped in `name="json"` with a payload of `{"name": "json", "arguments": {"steps": [{"step_id": 1, "tool_name": "...", "tool_args": {...}, "description": "..."}]}}`. Groq's API throws an HTTP 400 exception stating `attempted to call tool 'json' which was not in request.tools`, but embeds the full generated payload in `failed_generation`.
2. **Missing Adapter Extraction**: `common/llm_services/base_llm.py` lacked an adapter to intercept the 400 exception and extract `failed_generation` before falling back to string parsing re-invocations.
3. **Pydantic Schema Key Mismatch**: Groq's generated payload used key names `step_id`, `tool_name`, `tool_args`, and `description` instead of `id`, `tool`, `args`, and `rationale`. When Pydantic validation (`model_validate`) ran directly on the raw dictionary, it threw missing field validation errors for `id` and `tool`.

---

## D. Minimal Fix

The minimal fix was implemented strictly within the allowed file `common/llm_services/base_llm.py`:

1. **Added `_try_recover_structured(self, exc, schema)` to `LLM_Model`**:
   * Scans exception text for `failed_generation`.
   * Safely extracts and decodes the JSON payload regardless of quote escaping.
   * Performs field normalization mapping:
     * `step_id` / `id` $\rightarrow$ `id: str`
     * `tool_name` / `tool` / `action` $\rightarrow$ `tool: str`
     * `tool_args` / `args` / `arguments` $\rightarrow$ `args: dict`
     * `description` / `rationale` $\rightarrow$ `rationale: str`
   * Validates normalized dictionary into a valid `Plan` object via `schema.model_validate(norm_args)`.
2. **Updated `invoke_structured` in `LLM_Model`**:
   * On structured output invocation failure, calls `_try_recover_structured(exc, schema)` before falling back to string-parser re-invocations.

### Files Modified

* `common/llm_services/base_llm.py`

*(No other files modified).*

---

## E. Targeted Tests

Targeted adapter tests were executed for four representative question types:

| Test | Question Type | Representative Question | Selected Tool | Plan Recovery |
| :--- | :--- | :--- | :--- | :--- |
| **Test A** | Lookup | *How many nations competed in Sailing at the 2016 Summer Olympics – Women's RS:X?* | `graphrag__lookup` | **SUCCESS** |
| **Test B** | Temporal | *Who won the gold medal in the men's freestyle 82 kg wrestling event at the Summer Olympics held immediately before 1996?* | `graphrag__temporal_resolve` | **SUCCESS** |
| **Test C** | Aggregation | *According to the provided corpus, how many alpine skiing events at the 2014 Winter Olympics had more than 63 competitors?* | `graphrag__aggregate` | **SUCCESS** |
| **Test D** | Superlative | *According to the provided corpus, which sailing event at the 2000 Summer Olympics had the highest number of competitors?* | `graphrag__superlative` | **SUCCESS** |

---

## F. End-to-End Tool Dispatch

For each representative question, end-to-end dispatch through `Question` $\rightarrow$ `LLM Planner` $\rightarrow$ `Plan` $\rightarrow$ `Tool Registry` $\rightarrow$ `Phase 6 Deterministic Tool` $\rightarrow$ `StepResult` $\rightarrow$ `Executor` was verified against live TigerGraph Cloud:

```text
[Lookup]
  1. Adapter Plan Recovery: SUCCESS
  2. Selected Tool: graphrag__lookup
  3. Tool Args: {"event_title": "Sailing at the 2016 Summer Olympics – Women's RS:X"}
  4. Registered in Catalog: True
  5. Executor Dispatch: SUCCESS
  6. Phase 6 Live Result: 26

[Temporal]
  1. Adapter Plan Recovery: SUCCESS
  2. Selected Tool: graphrag__temporal_resolve
  3. Tool Args: {"event_name": "Wrestling at the Summer Olympics – Men's freestyle 82 kg", "season": "Summer", "reference_year": 1996, "relation": "before"}
  4. Registered in Catalog: True
  5. Executor Dispatch: SUCCESS
  6. Phase 6 Live Result: Kevin Jackson

[Aggregation]
  1. Adapter Plan Recovery: SUCCESS
  2. Selected Tool: graphrag__aggregate
  3. Tool Args: {"sport": "Alpine Skiing", "games": "2014 Winter Olympics", "threshold": 63, "comparison": ">"}
  4. Registered in Catalog: True
  5. Executor Dispatch: SUCCESS
  6. Phase 6 Live Result: 4

[Superlative]
  1. Adapter Plan Recovery: SUCCESS
  2. Selected Tool: graphrag__superlative
  3. Tool Args: {"sport": "Sailing", "games": "2000 Summer Olympics", "metric": "competitors", "order": "highest"}
  4. Registered in Catalog: True
  5. Executor Dispatch: SUCCESS
  6. Phase 6 Live Result: Sailing at the 2000 Summer Olympics – Soling
```

All four Phase 6 deterministic Olympic tools are verified callable and fully functional through the standard agentic dispatch path.

---

## G. Regression Checks

* **12-Tool Catalog**: Unchanged (4 Olympic deterministic tools + 8 standard tools).
* **Phase 6 Olympic Tools (`olympic_tools.py`)**: Unchanged (78/78 tests preserved).
* **Qwen Retrieval (`HybridRetriever.py`, `SimilarityRetriever.py`)**: Unchanged.
* **`pass_qtype=False` Configuration**: Preserved.
* **Existing Executor (`agentic_executor.py`)**: Unchanged and 100% compatible.
* **GSQL Queries & Schema**: Unchanged.
* **Qwen Vector Embeddings**: Unchanged.
* **TigerGraph Cloud Graph State**: Unchanged.

---

## H. Exact Next Gate

The integration repair is complete and verified. The system is ready for the rerun of the 100-question Phase 7 agentic benchmark once the Groq API daily rate limit (200,000 TPD) window resets.
