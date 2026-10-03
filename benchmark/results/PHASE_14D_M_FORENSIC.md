# PHASE 14D-M — OFFLINE FORENSICS OF CURRENT 5Q RESULT

**FINAL CLASSIFICATION**: `MIXED_FAILURE`  
**API CALLS MADE**: `0`  
**LIVE QUESTIONS EXECUTED**: `0`  
**PRODUCTION FILES MODIFIED**: `0`  

---

## 1. Executive Summary & Classification

A comprehensive offline forensic audit was conducted on the 5-question benchmark results (`pub-001` through `pub-005`).

### Overall Classification: `MIXED_FAILURE`
1. **`pub-001` & `pub-003`**: `EVALUATOR_PATH_FAILURE`  
   - In original Gate 10 artifacts, `pub-001` ("five" vs "5") and `pub-003` ("eight" vs "8") were marked `False` because word-number normalization was missing from `unified_evaluator.py` at the time of that run.
   - With the active Phase 14D-K evaluator (`convert_word_numbers`), offline re-scoring proves `pub-001` and `pub-003` evaluate to **`True`** (100% correct).
2. **`pub-005`**: `PARSER_FAILURE` / `SYNTHESIS_FAILURE` (in fallback/unauthenticated runs) vs `PASS` (in authenticated AIRouter runs).
   - In Gate 10 AIRouter run, `pub-005` produced `"The gold medal in the event held at the Olympic Weightlifting Gymnasium on 20 September 1988 was won by Naim Süleymanoğlu of Turkey."`, which evaluates to **`True`**.
   - In unauthenticated fallback runs, LLM planner parser failure triggered keyword fallback, and synthesis parser failure produced `"(no answer produced)"`.
3. **Rescored 5Q Accuracy**: **`5/5 (100.0%)`** when evaluated through the active Phase 14D-K `unified_evaluator.py`.

---

## 2. Task-by-Task Diagnostic Findings

### Task 1 — Evaluator Path & Normalization Audit
- **Runner Evaluator Import**: `scratch/run_gate10_5q_airouter_smoke.py` imports `normalize_answer` and `compute_correctness` from `benchmark.unified_evaluator`.
- **Phase 14D-K Normalization Status**: **ACTIVE**. Lines 9–17 of `benchmark/unified_evaluator.py` define `_WORD_NUMBERS` and `convert_word_numbers(text)` via `re.sub(rf'\b{word}\b', num, text, flags=re.IGNORECASE)`.
- **Offline Reproduction**:
  - `normalize_answer("five")` $\rightarrow$ `"5"` (`normalize("five") == normalize("5")` $\rightarrow$ **TRUE**)
  - `normalize_answer("eight")` $\rightarrow$ `"8"` (`normalize("eight") == normalize("8")` $\rightarrow$ **TRUE**)
  - `compute_correctness("five biathlon events...", "5")` $\rightarrow$ **TRUE**
  - `compute_correctness("eight shooting events...", "8")` $\rightarrow$ **TRUE**

### Task 2 — `pub-005` Forensic Audit
- **Planned Tool**: `graphrag__hybrid_search`
- **Actual Tool**: `graphrag__hybrid_search`
- **Tool Arguments**: `{"question": "Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?"}`
- **Tool Output**: Retrieved Infobox & text chunk `Q1178652_chunk_0` containing Naim Süleymanoğlu winning gold in 60 kg weightlifting on 20 September 1988 at Olympic Weightlifting Gymnasium.
- **Evidence Returned**: YES (`Q1178652_chunk_0`).
- **Synthesis & Parser Behavior**:
  - In authenticated Gate 10 run: Synthesis generated `"The gold medal... was won by Naim Süleymanoğlu of Turkey."` $\rightarrow$ Evaluator: **TRUE**.
  - In unauthenticated fallback run: LLM parser failure triggered raw-output salvage, which failed to parse a response payload and returned fallback string `"(no answer produced)"`.

### Task 3 — Comparison with Known-Good `pub-004`
- **Triage**: Passed / skipped.
- **Planning**: Selected `graphrag__superlative` with `{"sport":"athletics","games":"2008 Summer Olympics"}`.
- **Tool Execution**: GSQL query executed on TigerGraph.
- **Evidence**: `Athletics at the 2008 Summer Olympics – Men's marathon`, 95 competitors.
- **Synthesis**: Generated `"According to the provided corpus, the athletics event at the 2008 Summer Olympics with the highest number of competitors was Athletics at the 2008 Summer Olympics – Men's marathon, which had 95 competitors."`
- **Verdict**: **100% Match** across Phase 14D-I and Gate 10 runs.

### Task 4 — Embedding Dimension Audit
- Log message `qwen3-embedding:0.6b with dimensions=1536` is an informational log line from Ollama embedding service initialization.
- `server_config.json` explicitly sets `"output_dimensionality": 1024` and vector search in `graphrag__hybrid_search` successfully queries the existing 1024-dim vector index in TigerGraph.
- **Causal Relationship to `pub-005`**: **NONE**. Vector retrieval retrieved relevant gold chunks for `pub-005` and `pub-002`.

---

## 3. Comprehensive 5Q Diagnostic Summary Table

| QID | Qtype | Prediction in Gate 10 Artifact | Gold Answer | Original Score | Current `unified_evaluator` Score | Diagnosis |
|---|---|---|---|---|---|---|
| `pub-001` | aggregation | `"five biathlon events..."` | `["5"]` | FALSE | **TRUE** | `EVALUATOR_PATH_FAILURE` (Word-number normalization missing in original run, resolved in 14D-K) |
| `pub-002` | temporal | `"won by Chen Ding"` | `["Chen Ding"]` | TRUE | **TRUE** | `PASS` |
| `pub-003` | aggregation | `"eight shooting events..."` | `["8"]` | FALSE | **TRUE** | `EVALUATOR_PATH_FAILURE` (Word-number normalization missing in original run, resolved in 14D-K) |
| `pub-004` | superlative | `"Men's marathon..."` | `["Athletics at... Men's marathon"]` | TRUE | **TRUE** | `PASS` |
| `pub-005` | multi_hop | `"won by Naim Süleymanoğlu..."` | `["Naim Süleymanoğlu"]` | TRUE | **TRUE** | `PASS` in Gate 10; `PARSER_FAILURE` in unauthenticated fallback runs |

**Rescored Total Accuracy**: **`5/5 (100.0%)`**

---

## 4. Exact Minimal Next Action

1. **Do NOT patch production code or evaluator**.
2. **Obtain valid AIRouter API key** starting with `sk-air-v1-...` or set valid provider environment credentials.
3. Once valid credentials are provided, execute the live 25Q pilot benchmark.
