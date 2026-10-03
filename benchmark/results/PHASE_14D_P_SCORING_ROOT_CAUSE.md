# PHASE 14D-P — 5Q SCORING ROOT-CAUSE REPAIR REPORT

**Final Status**: `PASS — ROOT CAUSE FOUND AND MINIMAL REPAIR VERIFIED OFFLINE`  
**API Calls**: `0`  
**Live Questions**: `0`  
**Phase 12 Modified**: `NO`  
**Phase 13 Modified**: `NO`  
**TigerGraph Modified**: `NO`  
**Embeddings Modified**: `NO`  
**Secrets Exposed**: `NO`

---

## 1. Executive Summary & Root Cause Finding

A comprehensive offline source code and artifact forensic audit was conducted on the Gate-10 5Q scoring discrepancy.

### Primary Root Cause Findings:
1. **Historical Discrepancy Origin**: The live Gate-10 5Q AIRouter smoke run (`scratch/run_gate10_5q_airouter_smoke.py`) was executed **prior to Phase 14D-K**, when `benchmark/unified_evaluator.py` lacked number-word to digit conversion (`convert_word_numbers`).
   - For `pub-001`, the LLM synthesized `"five biathlon events"`, but the evaluator checked `norm_gold` `"5"` in `norm_pred` `"according to provided corpus five biathlon events..."` without converting `"five"` to `"5"`, resulting in `False`.
   - For `pub-003`, the LLM synthesized `"eight shooting events"`, but the evaluator checked `norm_gold` `"8"` in `norm_pred` `"according to provided corpus eight shooting events..."` without converting `"eight"` to `"8"`, resulting in `False`.

2. **Evaluator Edge-Case Vulnerabilities Repaired**:
   - **Digit Collision Failure**: In `compute_correctness()`, naive substring matching (`norm_gold in norm_pred`) caused single digits like `"8"` to match inside `"18"` (`'8' in '18'` $\rightarrow$ `True`).
   - **Hyphenated Number Normalization**: Punctuation stripping without space conversion caused `"twenty-five"` to become `"twentyfive"`, missing the word boundary check `\btwenty\b`.

3. **Repaired Evaluator Verification**:
   - Updated `_WORD_NUMBERS` with compound mappings (`twenty-one` .. `ninety-nine` $\rightarrow$ `21` .. `99`).
   - Added dash/hyphen normalization (`normalize_dashes`) to `normalize_answer()`.
   - Enhanced `compute_correctness()` to use strict token word-boundary matching (`re.search(rf'\b{re.escape(norm_gold)}\b', norm_pred)`).
   - Rescoring the exact saved Gate-10 live artifact (`PHASE_14D_GATE10_5Q_RESULTS.jsonl`) produces **5/5 (100%)**.

---

## 2. Data Flow Trace

```
Gold Answer ("5" / "8")
      │
      ▼
Deterministic Aggregate Tool (graphrag__aggregate)
      │
      ▼
Tool Result (5 / 8)
      │
      ▼
Synthesis ("... five biathlon events ..." / "... eight shooting events ...")
      │
      ▼
Final Answer
      │
      ▼
Repaired Unified Evaluator (normalize_answer + word boundary match)
      │
      ▼
TRUE (pub-001: 5/5, pub-003: 5/5)
```

| Question ID | QType | Gold Answer | Tool Selected & Result | Generated Final Answer | Historical Gate-10 Score | Repaired Evaluator Score |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **pub-001** | aggregation | `["5"]` | `graphrag__aggregate` $\rightarrow$ `5` | *"According to the provided corpus, five biathlon events at the 2018 Winter Olympics had more than 73 competitors."* | `False` | **`True`** |
| **pub-002** | temporal | `["Chen Ding"]` | `graphrag__temporal_resolve` | *"The gold medal in the men's 20 kilometres walk at the Summer Olympics held immediately before 2016 was won by Chen Ding."* | `True` | **`True`** |
| **pub-003** | aggregation | `["8"]` | `graphrag__aggregate` $\rightarrow$ `8` | *"According to the provided corpus, eight shooting events at the 2004 Summer Olympics had more than 37 competitors."* | `False` | **`True`** |
| **pub-004** | superlative | `["Athletics at 2008..."]` | `graphrag__superlative` | *"According to the provided corpus, the athletics event at the 2008 Summer Olympics with the highest number of competitors was Athletics at the 2008 Summer Olympics – Men's marathon..."* | `True` | **`True`** |
| **pub-005** | multi-hop | `["Naim Süleymanoğlu"]` | `graphrag__hybrid_search` | *"The gold medal in the event held at the Olympic Weightlifting Gymnasium on 20 September 1988 was won by Naim Süleymanoğlu of Turkey."* | `True` | **`True`** |

---

## 3. Runner & Evaluator Binding Audit

- **Runner Script**: `scratch/run_gate10_5q_airouter_smoke.py`
- **Import Statement**: `from benchmark.unified_evaluator import normalize_answer, compute_correctness`
- **Execution Line**: Line 64: `norm_corr = compute_correctness(ans, gold_str) if not is_app_failure else False`
- **Binding Confirmation**: The Gate-10 runner dynamically imports and calls `compute_correctness` directly from `benchmark/unified_evaluator.py`. When `run_gate10_5q_airouter_smoke.py` runs, it immediately uses the updated evaluator logic.

---

## 4. Minimal Code Modifications

### File: `benchmark/unified_evaluator.py`

```python
# Added _TENS and _UNITS compound mappings for number words (21..99)
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}
_UNITS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9
}

_WORD_NUMBERS = {}
for _t_word, _t_val in _TENS.items():
    for _u_word, _u_val in _UNITS.items():
        _WORD_NUMBERS[f"{_t_word} {_u_word}"] = str(_t_val + _u_val)
        _WORD_NUMBERS[f"{_t_word}-{_u_word}"] = str(_t_val + _u_val)

# Added dash/hyphen normalization step
def normalize_dashes(text):
    return re.sub(r'[\-\u2010\u2011\u2012\u2013\u2014\u2015]', ' ', text)

# Updated compute_correctness to use token word-boundary matching
def compute_correctness(prediction: str, gold: str) -> bool:
    norm_pred = normalize_answer(prediction)
    norm_gold = normalize_answer(gold)
    if not norm_gold or not norm_pred:
        return False
    if norm_gold == norm_pred:
        return True
    pattern_gold = rf'\b{re.escape(norm_gold)}\b'
    pattern_pred = rf'\b{re.escape(norm_pred)}\b'
    return bool(re.search(pattern_gold, norm_pred) or re.search(pattern_pred, norm_gold))
```

---

## 5. Validation Results

1. **Unit Test Suite Execution**:
   - Test File: `scratch/test_evaluator_number_word_normalization.py`
   - Total Tests: `16/16 PASS`
   - Key Tests Passed:
     - `test_01` .. `test_04`: `five` $\rightarrow$ `5`, `eight` $\rightarrow$ `8`, `one` $\rightarrow$ `1`, `ten` $\rightarrow$ `10` (**PASS**)
     - `test_05` .. `test_06`: `"five biathlon events"` vs `"5"`, `"eight shooting events"` vs `"8"` (**PASS**)
     - `test_07` .. `test_09`: `"stone"`, `"someone"`, `"eighteen"` $\rightarrow$ `"18"` (no corruption) (**PASS**)
     - `test_13`: Saved 5Q offline rescore $\rightarrow$ **5/5 (100%) PASS**
     - `test_14`: Token boundary safety (`"eighteen"` vs `"8"` $\rightarrow$ `False`, `"fiveth"` vs `"5"` $\rightarrow$ `False`) (**PASS**)
     - `test_15`: Hyphenated compound numbers (`"twenty-five"` $\rightarrow$ `"25"`) (**PASS**)
     - `test_16`: Pub-001 & Pub-003 exact phrasings (**PASS**)

2. **Python Syntax Compilation**:
   - Command: `python -m py_compile benchmark/unified_evaluator.py scratch/test_evaluator_number_word_normalization.py`
   - Outcome: `0 errors / PASS`

3. **Network / AIRouter Isolation**:
   - `git diff` confirms 0 network calls, 0 LLM invocations, and 0 external dependencies added.

---

## 6. Verification Summary

```
OFFLINE SCORING PATH REPAIR VERIFIED
Rescored Gate-10 5Q Accuracy: 5/5 (100%)
pub-001: TRUE
pub-002: TRUE
pub-003: TRUE
pub-004: TRUE
pub-005: TRUE
```
