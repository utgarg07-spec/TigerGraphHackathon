# PHASE 14D-X — LINE 863 AIRouter DETECTION REPAIR REPORT

## Executive Summary

Phase 14D-X implements the precise line-863 fix identified during the forensic source audit to resolve the synthesis-path empty content defect (`pub-003`).

1. **Line 863 Provider Detection Fix (`common/llm_services/base_llm.py`)**: Updated `is_openrouter` inside `invoke_with_parser()` so AIRouter (`base_url="https://api.airouter.in/v1"`) triggers the direct chat completions bypass path using `raw_msgs` and prompt format instructions, establishing full parity with `invoke_structured()` (line 1071).
2. **Fix B Preservation**: Retained Fix B in `graphrag/app/agent/agentic_executor.py` unchanged.
3. **No Planner/Executor/Evaluator Redesign**: Zero changes were made to planner, executor, retrieval, GSQL, docker-compose, or evaluator code.

---

## Code Modification Details

- **File**: `common/llm_services/base_llm.py`
- **Method**: `invoke_with_parser()` (Line 863)
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

---

## Mandatory Offline Validation Results

1. **Syntax Compilation Check**:
   - `python -m py_compile common/llm_services/base_llm.py`
   - Exit Code: `0`

2. **Container Unit Test Suite (`scratch/test_phase14d_x_line863_validation.py`)**:
   - Executed inside Docker: `docker exec -w /code graphrag python scratch/test_phase14d_x_line863_validation.py`
   - Exit Code: `0`
   - **Pass 1**: `invoke_with_parser()` (Line 863) & `invoke_structured()` (Line 1071) recognize AIRouter (`is_openrouter=True`).
   - **Pass 2**: OpenRouter behavior remains unchanged (`is_openrouter=True`).
   - **Pass 3**: Standard OpenAI behavior remains unchanged (`is_openrouter=False`).
   - **Pass 4**: `AIRouter` service configuration and `ChatOpenAI(max_retries=0)` retry-owner architecture remain untouched.

---

## Verification & Constraints Report

- **Exact Production Files Modified**: `common/llm_services/base_llm.py` (Line 863)
- **Fix B in `agentic_executor.py`**: Retained unchanged.
- **Production Files Outside Line 863 Changed**: **NO**
- **API Calls Executed**: `0`
- **Live Questions Executed**: `0`
- **Phase 12/13 Files Modified**: **NO**
- **Embeddings/GSQL/Retrieval Modified**: **NO**
- **Evaluator Modified**: **NO**
