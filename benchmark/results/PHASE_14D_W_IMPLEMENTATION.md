# PHASE 14D-W — MINIMUM PRODUCTION FIXES IMPLEMENTATION REPORT

## Executive Summary

Phase 14D-W implements the two minimum production fixes identified and proven during the Phase 14D-V forensic source audit:

1. **Fix A (AIRouter Structured Output Bypass)**: Configured `common/llm_services/base_llm.py` so `AIRouter` model invocations follow the direct-chat `PydanticOutputParser` path rather than attempting unsupported OpenAI native function/tool calling via `ChatOpenAI.with_structured_output()`.
2. **Fix B (Structural Retrieve Question Protection)**: Configured `graphrag/app/agent/agentic_executor.py` so argument binding resolution does **not** overwrite an existing non-empty string question with a dictionary context (`S1.context`).

---

## Detailed Code Modifications

### 1. Fix A — AIRouter Structured Output Bypass (`common/llm_services/base_llm.py`)

- **Location**: `common/llm_services/base_llm.py` inside `invoke_structured()` (Line 1071).
- **Exact Code Change**:
  ```python
  is_openrouter = (
      "openrouter" in str(getattr(llm_instance, "openai_api_base", "") or "").lower() or
      "openrouter" in str(getattr(getattr(llm_instance, "root_client", None), "base_url", "")).lower() or
      "airouter" in str(getattr(llm_instance, "openai_api_base", "") or "").lower() or
      "airouter" in str(getattr(getattr(llm_instance, "root_client", None), "base_url", "")).lower() or
      getattr(self, "provider_name", "") == "airouter"
  )
  ```
- **Rationale**: Previously, `is_openrouter` only checked for `"openrouter"` in the base URL string. AIRouter (`base_url = "https://api.airouter.in/v1"`) fell into `llm_instance.with_structured_output(schema)`, which transmitted OpenAI tool payloads to `openai/gpt-oss-20b` and produced `HTTP 200` with `content=''`. With this fix, AIRouter uses prompt-based format instructions directly.

### 2. Fix B — Structural Retrieve Argument Binding Protection (`graphrag/app/agent/agentic_executor.py`)

- **Location**: `graphrag/app/agent/agentic_executor.py` inside `execute_plan()` (Lines 178-182).
- **Exact Code Change**:
  ```python
  for arg_name, ref in (step.arg_bindings or {}).items():
      val = _resolve_path(results, ref)
      if val is not None:
          if arg_name == "question" and isinstance(val, dict) and isinstance(args.get("question"), str) and args["question"].strip():
              continue
          args[arg_name] = val
  ```
- **Rationale**: Prevents `arg_bindings` (e.g., `{"question": "S1.context"}`) from assigning a `dict` payload over a valid, non-empty `question` string already assigned to a retrieval tool step, preventing `Pydantic.ValidationError` on `StructuralRetrieveArgs`.

---

## Mandatory Offline Validation Results

1. **Compilation Check**:
   - `python -m py_compile common/llm_services/base_llm.py graphrag/app/agent/agentic_executor.py`
   - Exit Code: `0`

2. **Container Unit Testing (`scratch/test_phase14d_w_offline_validation.py`)**:
   - Executed inside Docker: `docker exec -w /code graphrag python scratch/test_phase14d_w_offline_validation.py`
   - Exit Code: `0`
   - **Fix A Pass 1**: AIRouter `base_url="https://api.airouter.in/v1"` triggers bypass path (`is_openrouter=True`).
   - **Fix A Pass 2**: OpenRouter `base_url="https://openrouter.ai/api/v1"` preserves existing bypass path (`is_openrouter=True`).
   - **Fix A Pass 3**: Standard OpenAI `base_url="https://api.openai.com/v1"` preserves default native path (`is_openrouter=False`).
   - **Fix B Pass 1**: Existing string question preserved when binding resolves to `dict` `S1.context`.
   - **Fix B Pass 2**: Existing string question overwritten when binding resolves to `str` `S2.context`.
   - **Fix B Pass 3**: No existing question $\rightarrow$ `dict` assigned as before.
   - **Fix B Pass 4**: Unrelated argument binding preserves existing behavior.

---

## Final Verification Checklist

- **Exact Production Files Modified**:
  1. `common/llm_services/base_llm.py`
  2. `graphrag/app/agent/agentic_executor.py`
- **Production Files Outside Target Changed**: **NO**
- **API Calls**: `0`
- **Live Questions Executed**: `0`
- **Phase 12/13 Files Modified**: **NO**
- **Phase 6 Files Modified**: **NO**
- **Embeddings/GSQL/Retrieval Files Modified**: **NO**
- **Docker-Compose Modified**: **NO**
- **Evaluator Modified**: **NO**
- **Diagnostic Runner Modified**: **NO**
