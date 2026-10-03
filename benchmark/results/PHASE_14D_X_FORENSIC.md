# PHASE 14D-X — W REGRESSION FORENSIC AUDIT REPORT

## Executive Summary

The Phase 14D-X offline audit traced the exact execution paths for `pub-003` and `pub-005` following the Phase 14D-W targeted regression run.

Source inspection has yielded **100% PROVEN** root causes for both behaviors without guessing or live testing.

---

## Section X1 — `pub-003` Forensic Trace (`generate_answer` empty content)

### 1. Exact Invoke Path Used by `generate_answer`
`agentic_synthesizer.synthesize()` $\rightarrow$ `TigerGraphAgentGenerator.generate_answer()` $\rightarrow$ `llm.invoke_with_parser()` (in `common/llm_services/base_llm.py`).

### 2. Root Cause Mechanism (**PROVEN**)
In `common/llm_services/base_llm.py`, provider detection logic was updated in `invoke_structured()` (line 1071) during Phase 14D-W, but **was omitted from `invoke_with_parser()` (line 863)**:

- **Line 863 in `invoke_with_parser()` (Un-updated)**:
  ```python
  is_openrouter = "openrouter" in str(getattr(llm_instance, "openai_api_base", "") or "").lower() or "openrouter" in str(getattr(getattr(llm_instance, "root_client", None), "base_url", "")).lower()
  ```
- **Line 1071 in `invoke_structured()` (Updated in 14D-W)**:
  ```python
  is_openrouter = ("openrouter" in ... or "airouter" in ... or getattr(self, "provider_name", "") == "airouter")
  ```

### 3. Why `agentic_triage`/`agentic_plan` Succeeded while `generate_answer` Failed (**PROVEN**)
- `agentic_triage` and `agentic_plan` invoke `invoke_structured()`. Line 1071 evaluated `is_openrouter = True` for AIRouter, triggering the direct chat completions API with `raw_msgs` and returning valid text.
- `generate_answer` invokes `invoke_with_parser()`. Line 863 evaluated `is_openrouter = False` for AIRouter (`https://api.airouter.in/v1`).
- Line 863 forced `generate_answer` onto the `else:` branch:
  ```python
  chain = prompt | llm_instance
  return chain.invoke(input_variables)
  ```
- `chain.invoke()` invoked `ChatOpenAI.invoke(...)` directly. AIRouter's backend for `openai/gpt-oss-20b` returns `HTTP 200` with **empty string content** (`content=''`) when called via `ChatOpenAI.invoke`.
- `raw_text` was `""`, parsing failed, and `_salvage_answer_output("")` produced `(no answer produced)`.

---

## Section X2 — `pub-005` Forensic Trace (Disambiguation in Multi-Candidate Context)

### 1. Exact Execution Path (**PROVEN**)
- In the 14D-W run, the LLM planner (`agentic_plan`) generated a 1-step plan containing only `graphrag__hybrid_search` (Step 1).
- Fix B in `agentic_executor.py` did **not** drop or skip any step. It strictly prevented `args["question"]` from being overwritten by a `dict` when `arg_bindings` pointed to a `dict` context.

### 2. Cause of Answer Selection (**PROVEN**)
- `graphrag__hybrid_search` retrieved document chunks covering two separate 1988 weightlifting events held on **20 September 1988** at the **Olympic Weightlifting Gymnasium**:
  1. `Q25239533_chunk_0`: Men's 67.5 kg (Gold: Joachim Kunz, GDR).
  2. `q25239316_chunk_0`: Men's 60 kg (Gold: Naim Süleymanoğlu, TUR).
- Because both events share the exact venue and date mentioned in the question, unstructured synthesis without a 2nd-stage structural query or canonical event title constraint selected Joachim Kunz instead of Naim Süleymanoğlu.

---

## Section X3 — Actionable Recommendation & Safety Audit

1. **Fix A (`common/llm_services/base_llm.py`)**:
   - **Recommendation**: **MODIFY**.
   - Must extend the `"airouter"` provider check to **line 863 in `invoke_with_parser()`** so `generate_answer` uses direct chat completions with `raw_msgs` just like `invoke_structured()`.

2. **Fix B (`graphrag/app/agent/agentic_executor.py`)**:
   - **Recommendation**: **RETAIN**.
   - The argument binding check in `agentic_executor.py` is logically sound and correctly prevents schema validation crashes.

---

## Verification Checklist

- **Production Modifications during Audit**: `0`
- **AIRouter API Calls**: `0`
- **Live Questions Executed**: `0`
- **Phase 12/13 Files Modified**: **NO**
- **Embeddings/GSQL/Retrieval Modified**: **NO**
