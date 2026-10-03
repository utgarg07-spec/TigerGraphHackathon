# PHASE 14D-L-C — 25Q RUNNER PREFLIGHT FAILURE FORENSICS REPORT

**PHASE 14D-L-C STATUS**: `PASS`

| Parameter | Value |
|---|---|
| **ROOT CAUSE** | `base_llm.MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL` attribute error (variable is scoped locally inside `_execute_with_fallback`) |
| **AUTHORITATIVE PROVIDER ATTEMPT LIMIT LOCATION** | `common/llm_services/base_llm.py` (`LLM_Model._execute_with_fallback` line 707) |
| **VALUE** | `2` |
| **RUNNER FIX** | Updated `scratch/run_phase14d_l_25q_pilot.py` to inspect `_execute_with_fallback` source directly without touching production files |
| **API CALLS** | `0` |
| **LIVE QUESTIONS** | `0` |
| **PRODUCTION FILES MODIFIED** | `0` |
| **PHASE 12 MODIFIED** | `NO` |
| **PHASE 13 MODIFIED** | `NO` |
| **25Q RUNNER COMPILES** | `PASS` |
| **25Q QID SET** | `VALID` (25 unique QIDs, 5/5/5/5/5 distribution, 0 overlap with 5Q) |

---

## Forensic Analysis Details

1. **Gate 1 — Constant Location**:
   - `MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL = 2` is defined inside `LLM_Model._execute_with_fallback()` at line 707 of `common/llm_services/base_llm.py`.
   - It is enforced on lines 730 and 782 inside `_execute_with_fallback()`.
   - It is a function-scoped local variable, not a module-level variable on `common.llm_services.base_llm`.

2. **Gate 2 — Runner Incompatibility**:
   - `scratch/run_phase14d_l_25q_pilot.py` attempted to access `base_llm.MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL` as a module attribute.
   - Previous working runners (`run_phase14d_i_pub004.py`, `run_gate10_5q_airouter_smoke.py`) inspected telemetry from `get_provider_telemetry()` rather than querying a non-existent module constant.

3. **Gate 3 — Implementation Enforcement**:
   - `_execute_with_fallback()` strictly enforces $\le 2$ attempts per logical call (Attempt 1 on line 728, Attempt 2 on line 784). No third attempt is permitted.

4. **Gate 5 & 6 — Minimal Runner-Only Correction & Validation**:
   - `scratch/run_phase14d_l_25q_pilot.py` was updated to inspect the source code of `base_llm.LLM_Model._execute_with_fallback` using `inspect.getsource()` to extract `MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_CALL`.
   - Python compilation check: **PASS** (0 errors).
   - Preflight validation script: **PASS** (resolves to `2`).
   - QID set: **25 QIDs**, 5/5/5/5/5 distribution, **0 overlap** with Phase 14D 5Q.
   - **0 production files modified**.
