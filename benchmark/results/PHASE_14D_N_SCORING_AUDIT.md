# PHASE 14D-N — LIVE 5Q SCORING PATH AUDIT REPORT

**FINAL CLASSIFICATION**: `LIVE_SCORING_PATH_MISMATCH`  
**API CALLS MADE**: `0`  
**LIVE QUESTIONS EXECUTED**: `0`  
**PRODUCTION FILES MODIFIED**: `0`  

---

## 1. Executive Summary & Root Cause

A detailed offline code-path trace was executed to determine why the historical live Gate 10 5Q run produced a `3/5` score (`pub-001=FALSE`, `pub-003=FALSE`), while rescoring the exact saved outputs using the current `benchmark/unified_evaluator.py` produces `5/5` (`100.0%`).

### Classification: `LIVE_SCORING_PATH_MISMATCH`
- **Root Cause**: The historical Gate 10 live benchmark run (`PHASE_14D_GATE10_5Q_RESULTS.jsonl`) was executed against a **pre-Phase 14D-K** version of `benchmark/unified_evaluator.py` that did not perform word-number normalization (`"five"` $\rightarrow$ `"5"`, `"eight"` $\rightarrow$ `"8"`).
- **Current Evaluator State**: In Phase 14D-K, `convert_word_numbers()` was integrated into `benchmark/unified_evaluator.py`. The live runner (`scratch/run_gate10_5q_airouter_smoke.py`) imports `normalize_answer` and `compute_correctness` dynamically from `benchmark.unified_evaluator`.
- **Rescoring Verification**: When the exact predictions saved in `PHASE_14D_GATE10_5Q_RESULTS.jsonl` are evaluated using the current `benchmark/unified_evaluator.py`, all 5 questions evaluate to **`TRUE`** (`5/5`, `100.0%`).

---

## 2. Step-by-Step Code Path Trace

### A. Question `pub-001` (Aggregation)
- **Raw Prediction**: `"According to the provided corpus, five biathlon events at the 2018 Winter Olympics had more than 73 competitors."`
- **Gold Answer**: `["5"]` (`gold_str = "5"`)
- **Live Gate 10 Code Path (Pre-14D-K Evaluator)**:
  - `normalize_answer(ans)` $\rightarrow$ `"according to provided corpus five biathlon events 2018 winter olympics had more than 73 competitors"`
  - `normalize_answer("5")` $\rightarrow$ `"5"`
  - `"5" in "according to provided corpus five..."` $\rightarrow$ **`False`**
  - Live Gate 10 displayed `Acc: False`.
- **Current Evaluator Code Path (Post-14D-K Evaluator)**:
  - `convert_word_numbers("five")` $\rightarrow$ `"5"`
  - `normalize_answer(ans)` $\rightarrow$ `"according to provided corpus 5 biathlon events 2018 winter olympics had more than 73 competitors"`
  - `normalize_answer("5")` $\rightarrow$ `"5"`
  - `"5" in "according to provided corpus 5..."` $\rightarrow$ **`True`**
  - Current Evaluator displays `Acc: True`.

---

### B. Question `pub-003` (Aggregation)
- **Raw Prediction**: `"According to the provided corpus, eight shooting events at the 2004 Summer Olympics had more than 37 competitors."`
- **Gold Answer**: `["8"]` (`gold_str = "8"`)
- **Live Gate 10 Code Path (Pre-14D-K Evaluator)**:
  - `normalize_answer(ans)` $\rightarrow$ `"according to provided corpus eight shooting events 2004 summer olympics had more than 37 competitors"`
  - `normalize_answer("8")` $\rightarrow$ `"8"`
  - `"8" in "according to provided corpus eight..."` $\rightarrow$ **`False`**
  - Live Gate 10 displayed `Acc: False`.
- **Current Evaluator Code Path (Post-14D-K Evaluator)**:
  - `convert_word_numbers("eight")` $\rightarrow$ `"8"`
  - `normalize_answer(ans)` $\rightarrow$ `"according to provided corpus 8 shooting events 2004 summer olympics had more than 37 competitors"`
  - `normalize_answer("8")` $\rightarrow$ `"8"`
  - `"8" in "according to provided corpus 8..."` $\rightarrow$ **`True`**
  - Current Evaluator displays `Acc: True`.

---

### C. Question `pub-005` (Multi-hop)
- **Raw Prediction (Gate 10 AIRouter Live)**: `"The gold medal in the event held at the Olympic Weightlifting Gymnasium on 20 September 1988 was won by Naim Süleymanoğlu of Turkey."`
- **Gold Answer**: `["Naim Süleymanoğlu"]` (`gold_str = "Naim Süleymanoğlu"`)
- **Live Gate 10 Code Path**:
  - `normalize_answer(ans)` $\rightarrow$ `"gold medal event held at olympic weightlifting gymnasium 20 september 1988 was won by naim süleymanoğlu of turkey"`
  - `normalize_answer(gold_str)` $\rightarrow$ `"naim süleymanoğlu"`
  - `"naim süleymanoğlu" in "gold medal event held at..."` $\rightarrow$ **`True`**
  - Live Gate 10 displayed `Acc: True`.
- **Fallback / Unauthenticated Run Code Path**:
  - If AIRouter authentication fails (HTTP 401), prediction becomes `"I wasn't able to generate an answer for this question..."`.
  - `is_app_failure` check in runner sets `norm_corr = False`.

---

## 3. Discrepancy Reconciliation Matrix

| QID | Qtype | Live Gate 10 Result | Current `unified_evaluator` Rescore | Cause of Historical Mismatch |
|---|---|---|---|---|
| `pub-001` | aggregation | `FALSE` | **`TRUE`** | Historical Gate 10 evaluator lacked word-number conversion ("five" $\rightarrow$ "5") |
| `pub-002` | temporal | `TRUE` | **`TRUE`** | Correct match ("Chen Ding" $\rightarrow$ "Chen Ding") |
| `pub-003` | aggregation | `FALSE` | **`TRUE`** | Historical Gate 10 evaluator lacked word-number conversion ("eight" $\rightarrow$ "8") |
| `pub-004` | superlative | `TRUE` | **`TRUE`** | Correct match ("Men's marathon" $\rightarrow$ "Men's marathon") |
| `pub-005` | multi_hop | `TRUE` | **`TRUE`** | Correct match in Gate 10 AIRouter run ("Naim Süleymanoğlu" $\rightarrow$ "Naim Süleymanoğlu") |

**Total Rescored Score**: **`5/5 (100.0%)`**

---

## 4. Exact Next Action

1. **Do NOT modify runner or evaluator**. `scratch/run_gate10_5q_airouter_smoke.py` already imports `benchmark.unified_evaluator` directly.
2. The current `benchmark/unified_evaluator.py` containing Phase 14D-K word-number normalization is **authoritative** and active for all future live benchmark runs.
