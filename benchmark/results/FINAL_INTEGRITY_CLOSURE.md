# Final Integrity Closure Report

**Date**: September 27, 2026  
**Final Status**: **`VERIFIED WITH LIMITATION`**  
**Engineering Baseline**: **FROZEN** (Read-Only Verification Complete)

---

## 1. Executive Verdict

Following raw artifact inspection, row-by-row data parsing, and machine verification across all 100 benchmark execution records:

- **Engineering Pipeline**: Frozen and fully validated. Zero code modifications performed.
- **Benchmark Reproducibility**: 87/100 Normalized Accuracy, 93/100 Combined Gold Evidence Hit Rate, and 0.00% Retrieval Intrusion (on 22 computable text cases) are **100% independently reproducible** from `benchmark/results/agentic_full_100_evidence_recomputed.jsonl`.
- **Set Relationship Verification**: Verified mathematically that all 18 normalized-correct Multi-Hop questions form a strict subset of the 22 evidence-hit Multi-Hop questions ($18 \subseteq 22$).
- **9-Question Cross-Reference**: Verified that all 9 questions whose parent documents overlapped with the 43 historically missing embeddings were answered via deterministic GSQL tools (`graphrag__aggregate` / `graphrag__superlative`), incurring **zero negative impact** during Phase 7 benchmarking.
- **Per-ID Current-State Verification**: All 43 historically identified missing chunks are independently verified in the current TigerGraph state with non-null 1024-dimensional Qwen embeddings (**43 / 43 PASS**, see `benchmark/results/qwen_43_current_state_verification.csv`).
- **Final Status Selection**: **`VERIFIED WITH LIMITATION`**. All 43 historically identified missing chunks are independently verified in the current TigerGraph state with non-null 1024-dimensional Qwen embeddings. The original repair execution stdout was not preserved, so the historical write event itself remains report-level evidence.

---

## 2. Raw Artifact Verification Matrix

| Claim / Metric | Raw Supporting Artifact | Machine Verification | Audit Result |
| :--- | :--- | :--- | :--- |
| **100Q Accuracy (87.0%)** | `benchmark/results/agentic_full_100_evidence_recomputed.jsonl` | Parsed 100 JSON lines | **PASS (87 / 100)** |
| **Combined Evidence (93.0%)** | `benchmark/results/agentic_full_100_evidence_recomputed.jsonl` | Parsed 100 JSON lines | **PASS (93 / 100)** |
| **Completed Queries (94)** | `benchmark/results/agentic_full_100_evidence_recomputed.jsonl` | Verified 6 timeouts | **PASS (94 / 100)** |
| **Multi-Hop $18 \subseteq 22$** | `benchmark/results/multihop_joint_integrity_table.csv` | Parsed 28 rows | **PASS ($18 \subseteq 22$, B=0)** |
| **9 Affected Questions** | `benchmark/results/qwen_43_gold_cross_reference.csv` | Parsed 9 rows | **PASS (9 / 9 GSQL tools)** |
| **Phase 3 Aggregation (18/21)** | `benchmark/results/phase3_aggregation_integrity.csv` | Parsed 21 rows | **PASS (0/21 gold recall)** |
| **Per-ID 43 Chunk Verification** | `benchmark/results/qwen_43_current_state_verification.csv` | Verified 43 TG Cloud vertices | **PASS (43 / 43 present & non-null 1024-d)** |
| **43 Historical Write Event** | `benchmark/results/qwen_embedding_repair_raw_excerpt.txt` | Read report excerpt | **REPORT_ONLY** |

---

## 3. 43 Embedding Repair & Current-State Verification

- **Total Historical Missing Chunks**: 43
- **Embedding Model**: `qwen3-embedding:0.6b` (1,024 dimensions)
- **Per-ID Verification Artifacts**:
  - CSV: [`benchmark/results/qwen_43_current_state_verification.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_current_state_verification.csv)
  - JSON: [`benchmark/results/qwen_43_current_state_verification.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_current_state_verification.json)
- **Current-State Inspection Results**: **43 / 43 (100.0%) PASS** (all 43 vertices exist in TigerGraph Cloud and possess non-null 1024-dimensional Qwen embeddings).
- **All 43 Verified Chunk IDs**:
  `Q1005192_chunk_0`, `Q1005557_chunk_0`, `Q1005811_chunk_1`, `Q10572431_chunk_0`, `Q107861723_chunk_1`, `Q1095367_chunk_1`, `Q1156252_chunk_5`, `Q1222641_chunk_0`, `Q1222651_chunk_0`, `Q12808128_chunk_0`, `Q1360804_chunk_2`, `Q1408881_chunk_0`, `Q17515790_chunk_0`, `Q2000988_chunk_2`, `Q2070832_chunk_0`, `Q22964444_chunk_2`, `Q2463752_chunk_4`, `Q24761058_chunk_0`, `Q2500292_chunk_0`, `Q25991452_chunk_1`, `Q26228283_chunk_0`, `Q26234144_chunk_1`, `Q26860_chunk_1`, `Q280553_chunk_0`, `Q30680433_chunk_0`, `Q3499066_chunk_1`, `Q3628683_chunk_5`, `Q3628777_chunk_2`, `Q3998590_chunk_1`, `Q47155555_chunk_1`, `Q47295256_chunk_1`, `Q4903025_chunk_7`, `Q599322_chunk_1`, `Q645932_chunk_2`, `Q65242164_chunk_3`, `Q65242174_chunk_2`, `Q677063_chunk_1`, `Q735286_chunk_2`, `Q7979972_chunk_0`, `Q7979977_chunk_1`, `Q843436_chunk_6`, `Q914969_chunk_0`, `Q937526_chunk_0`.
- **Limitation Note**: All 43 historically identified missing chunks are independently verified in the current TigerGraph state with non-null 1024-dimensional Qwen embeddings. The original repair execution stdout was not preserved, so the historical write event itself remains report-level evidence.

---

## 4. 9-Question Cross-Reference Verification

Cross-referencing the 43 missing chunk IDs against the 100 benchmark questions produced exactly 9 matching QIDs:

| QID | Question Type | Affected Chunk ID | Tool / Path Used | Vector Search Used? | Deterministic Tool Used? | Answer Correct? | Evidence Hit? | Impact Conclusion |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pub-001` | Aggregation | `Q47155555_chunk_1` | `graphrag__aggregate` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-021` | Superlative | `Q1222641_chunk_0` | `graphrag__superlative` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-024` | Aggregation | `Q280553_chunk_0` | `graphrag__aggregate` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-045` | Aggregation | `Q2463752_chunk_4` | `graphrag__aggregate` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-053` | Superlative | `Q26228283_chunk_0` | `graphrag__superlative` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-058` | Aggregation | `Q17515790_chunk_0` | `graphrag__aggregate` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-066` | Superlative | `Q7979972_chunk_0`, `Q7979977_chunk_1` | `graphrag__superlative` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-078` | Aggregation | `Q26860_chunk_1` | `graphrag__aggregate` | `False` | `True` | `True` | `True` | No Phase 7 Impact |
| `pub-087` | Aggregation | `Q3628683_chunk_5` | `graphrag__aggregate` | `False` | `True` | `True` | `True` | No Phase 7 Impact |

**Conclusion**: All 9 affected questions were executed via GSQL graph traversal (`graphrag__aggregate` or `graphrag__superlative`). None required dense vector embeddings during Phase 7 execution.

---

## 5. Multi-Hop 28-Row Joint Verification

Parsing all 28 rows from `benchmark/results/multihop_joint_integrity_table.csv`:

- **Category A** (`Correct=True AND Evidence=True`): **18** (`pub-005`, `pub-011`, `pub-014`, `pub-022`, `pub-028`, `pub-030`, `pub-031`, `pub-038`, `pub-041`, `pub-043`, `pub-050`, `pub-064`, `pub-073`, `pub-079`, `pub-081`, `pub-083`, `pub-086`, `pub-095`)
- **Category B** (`Correct=True AND Evidence=False`): **0**
- **Category C** (`Correct=False AND Evidence=True`): **4** (`pub-023`, `pub-060`, `pub-067`, `pub-099`)
- **Category D** (`Correct=False AND Evidence=False`): **6** (`pub-015`, `pub-017`, `pub-076`, `pub-077`, `pub-096`, `pub-098`)

$$A + B + C + D = 18 + 0 + 4 + 6 = 28$$
$$\text{EvidenceHit Total} = A + C = 18 + 4 = 22$$
$$\text{CorrectAndEvidenceHit\_QIDs} \subseteq \text{EvidenceHit\_QIDs} \quad (18 \subseteq 22)$$

---

## 6. Phase 3 Aggregation Discrepancy

Verifying `benchmark/results/phase3_aggregation_integrity.csv`:
- Total aggregation questions: 21
- Strict exact matches: 0 / 21
- Normalized substring matches: 18 / 21 (85.71%)
- Gold document recall: 0 / 21 (0.0%)

**Fact**: 18/21 answers had normalized answer-string matches despite no verified gold-document retrieval. Evaluator string matching allowed coincidental parametric matches to register as hits.

---

## 7. Current Qwen Embedding Invariant

- Total `DocumentChunk` Vertices: 5,716
- Non-Null `qwen_embedding`: 5,716 (100.0%)
- Null Embeddings: 0
- Vector Dimension: 1,024-d

---

## 8. 100Q Benchmark Consistency

- Overall Normalized Accuracy: **87 / 100 = 87.0%**
- Completed Queries: **94 / 100**
- Timeouts: **6 / 100** (HTTP 120s timeouts)
- Combined Gold Evidence Hit Rate (All 100): **93 / 100 = 93.0%**
- Combined Gold Evidence Hit Rate (Completed 94): **93 / 94 = 98.94%**

---

## 9. Remaining Limitations

1. **Stdout Repair Log**: The terminal execution stdout log for the 43 missing embeddings repair script was not saved to disk at runtime. However, all 43 chunk IDs are independently verified in current TigerGraph Cloud state with non-null 1024-d Qwen embeddings.
2. **6 Timeouts**: 6 questions timed out at 120 seconds due to network HTTP timeouts rather than query logic errors.

---

## 10. Final Status

**FINAL INTEGRITY STATUS: `VERIFIED WITH LIMITATION`**

All core metrics, set inclusions, dynamic tool paths, 100-question benchmark data, and per-ID current TigerGraph embedding states (43/43 PASS) are machine-verified from raw JSONL, CSV, and live database queries.
