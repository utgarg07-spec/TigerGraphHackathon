# PHASE 14D-U HOTFIX — DIAGNOSTIC RUNNER TELEMETRY REPAIR

## Executive Summary

During the initial 5Q diagnostic run, all 5 questions failed with `AttributeError: 'StepResult' object has no attribute 'error'` inside `scratch/run_phase14d_u_5q_diagnostic.py` at line 133.

Source code inspection revealed that `StepResult` (defined in `common/py_schemas/schemas.py`) does **not** possess an `.error` attribute. Instead, its actual schema is:
```python
class StepResult(BaseModel):
    step_id: str
    ok: bool
    summary: str = ""
    context: Optional[object] = None
    citations: List[Dict] = []
```

The crash occurred because the telemetry hook intercepted execution after the production tool finished, attempted to access `step_res.error`, and raised an exception that aborted the question processing. This was a **diagnostic-runner defect** (Category C), not a failure of the underlying production Agentic pipeline.

---

## Actual StepResult Fields Discovered

- **`step_id`** (`str`): Unique identifier for the plan step (e.g., `"S1"`).
- **`ok`** (`bool`): Indicates step execution success (`True`) or failure (`False`).
- **`summary`** (`str`): Human-readable summary of the step result.
- **`context`** (`Optional[object]`): Context data returned by the tool (often a `dict` containing results or tool-level error details under `"error"`).
- **`citations`** (`List[Dict]`): Supporting sources gathered by retrieval.

---

## Runner-Only Changes (`scratch/run_phase14d_u_5q_diagnostic.py`)

1. **Repaired `hooked_run_step`**:
   - Replaced `error = step_res.error if step_res else ""` with safe extraction:
     - `success = bool(getattr(step_res, "ok", False))`
     - `error = ctx_err or summary or "step_ok_false"` if not `ok`.
   - Used `getattr(step, "tool", getattr(step, "name", "unknown_tool"))` for tool name access.
   - Wrapped argument serialization in `json.dumps(input_data, default=str)` inside `try/except`.

2. **Hardened All Telemetry Hooks**:
   - Wrapped pre-execution telemetry, post-execution telemetry, `log_event`, `heartbeat_worker`, `hooked_execute_with_fallback`, `hooked_parse_or_repair`, `hooked_salvage`, and `hooked_synthesize` in defensive `try/except` blocks.
   - If telemetry introspection fails, it logs `[DIAGNOSTIC_HOOK_ERROR] diagnostic_hook_error=true diagnostic_hook_message=<error>` and **NEVER** aborts or alters the main question execution.
   - Re-raises production exceptions (`prod_err`) unchanged when the underlying code fails, satisfying the requirement to preserve production failure semantics without swallowing errors.
   - Always returns the original `StepResult` object unchanged.

---

## Offline Validation Results

- **Syntax Compilation**: `python -m py_compile scratch/run_phase14d_u_5q_diagnostic.py` exited with code `0`.
- **Mock Unit Testing (`scratch/test_phase14d_u_hotfix_mock.py`)**:
  - **Test 1**: Successful step (`ok=True`) -> Passed. StepResult returned unchanged.
  - **Test 2**: Failing step (`ok=False`, no `.error` field) -> Passed. Handled gracefully without raising `AttributeError`.
  - **Test 3**: Step with missing/malformed attributes -> Passed. Processed safely.

---

## Compliance Audit

- **Modified Files**: `scratch/run_phase14d_u_5q_diagnostic.py`
- **Production Files Modified**: `0`
- **AIRouter API Calls**: `0`
- **Live Benchmark Questions Executed**: `0`
