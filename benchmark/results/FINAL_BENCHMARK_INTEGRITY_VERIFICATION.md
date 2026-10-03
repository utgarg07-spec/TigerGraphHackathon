# Final Benchmark Integrity & Raw Artifact Verification Report

**Date**: September 27, 2026  
**Final Integrity Status**: **VERIFIED WITH LIMITATION**  
**Engineering Changes**: **0** (Strictly Read-Only)  
**Authoritative Dataset**: 100 Serialized Benchmark Questions (`benchmark/results/agentic_full_100_evidence_recomputed.jsonl`)

---

## 1. Executive Summary & Verdict Determination

Following a comprehensive read-only audit of raw JSONL execution traces, GSQL queries, historical logs, and evaluation summaries:

- **Final Integrity Verdict**: **`VERIFIED WITH LIMITATION`**
- **Rationale**:
  1. All primary benchmark accuracy metrics (87.0% Normalized Match, 93.0% Combined Gold Evidence Hit Rate, 0.00% Retrieval Intrusion on 22 text cases) are **100% independently reproducible** from the raw line-by-line JSONL benchmark record (`agentic_full_100_evidence_recomputed.jsonl`).
  2. The 28 Multi-Hop questions, 21 Phase 3 aggregation questions, 9 cross-referenced chunk-affected questions, and 6 timeout questions were independently validated using raw per-question JSON records.
  3. **Limitation**: The historical repair of the 43 missing Qwen embeddings relies on report-level documentation (`benchmark/results/qwen_final_embedding_repair_report.md`) and pre/post query counts rather than a preserved raw execution `.log` file on disk.

---

## 2. Multi-Hop Joint Integrity Table (28 Questions)

### Intersection Analysis Across 28 Multi-Hop Questions

| Category | Description | Count | QID List |
| :--- | :--- | :--- | :--- |
| **Category A** | Correct (`normalized_match=True`) **AND** Evidence Hit (`gold_doc_hit=True`) | **18** | `pub-005`, `pub-011`, `pub-014`, `pub-022`, `pub-028`, `pub-030`, `pub-031`, `pub-038`, `pub-041`, `pub-043`, `pub-050`, `pub-064`, `pub-073`, `pub-079`, `pub-081`, `pub-083`, `pub-086`, `pub-095` |
| **Category B** | Correct (`normalized_match=True`) **AND** Evidence Miss (`gold_doc_hit=False`) | **0** | *None* |
| **Category C** | Incorrect (`normalized_match=False`) **AND** Evidence Hit (`gold_doc_hit=True`) | **4** | `pub-023`, `pub-060`, `pub-067`, `pub-099` |
| **Category D** | Incorrect (`normalized_match=False`) **AND** Evidence Miss (`gold_doc_hit=False`) | **6** | `pub-015`, `pub-017`, `pub-076`, `pub-077`, `pub-096`, `pub-098` |

### Key Integrity Questions Answered:

1. **Are all 18 normalized-correct Multi-Hop answers contained inside the 22 combined-evidence-hit questions?**  
   **YES.** All 18 normalized-correct answers belong to Category A ($18 \subseteq 22$). Category B is exactly 0.
2. **Which QIDs are correct but evidence-unverified?**  
   **None** (0 questions).
3. **Which QIDs have gold evidence but incorrect final answers?**  
   **4 QIDs**: `pub-023`, `pub-060`, `pub-067`, `pub-099` (caused by LLM answer formatting / entity translation mismatch during synthesis).
4. **Which QIDs are both incorrect and evidence-unverified?**  
   **6 QIDs**: `pub-015`, `pub-017`, `pub-076`, `pub-077`, `pub-096`, `pub-098` (5 of these 6 were 120-second HTTP timeouts).

- **Raw Data Artifacts Generated**:
  - [`benchmark/results/multihop_joint_integrity_table.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/multihop_joint_integrity_table.csv)
  - [`benchmark/results/multihop_joint_integrity_table.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/multihop_joint_integrity_table.json)

---

## 3. 43 Missing Qwen Embeddings Verification

- **Historical State**: 43 `DocumentChunk` vertices were temporarily missing `qwen_embedding` due to captive-portal HTTP interception during early ingestion.
- **Repair Status**: Repaired prior to final benchmark run.
- **Missing Chunk IDs (43 total)**:
  `Q1005192_chunk_0`, `Q1005557_chunk_0`, `Q1005811_chunk_1`, `Q10572431_chunk_0`, `Q107861723_chunk_1`, `Q1095367_chunk_1`, `Q1156252_chunk_5`, `Q1222641_chunk_0`, `Q1222651_chunk_0`, `Q12808128_chunk_0`, `Q1360804_chunk_2`, `Q1408881_chunk_0`, `Q17515790_chunk_0`, `Q2000988_chunk_2`, `Q2070832_chunk_0`, `Q22964444_chunk_2`, `Q2463752_chunk_4`, `Q24761058_chunk_0`, `Q2500292_chunk_0`, `Q25991452_chunk_1`, `Q26228283_chunk_0`, `Q26234144_chunk_1`, `Q26860_chunk_1`, `Q280553_chunk_0`, `Q30680433_chunk_0`, `Q3499066_chunk_1`, `Q3628683_chunk_5`, `Q3628777_chunk_2`, `Q3998590_chunk_1`, `Q47155555_chunk_1`, `Q47295256_chunk_1`, `Q4903025_chunk_7`, `Q599322_chunk_1`, `Q645932_chunk_2`, `Q65242164_chunk_3`, `Q65242174_chunk_2`, `Q677063_chunk_1`, `Q735286_chunk_2`, `Q7979972_chunk_0`, `Q7979977_chunk_1`, `Q843436_chunk_6`, `Q914969_chunk_0`, `Q937526_chunk_0`.
- **Evidence Level**: **`report_only`** (RAW REPAIR LOG NOT FOUND on disk; documented in [`benchmark/results/qwen_final_embedding_repair_report.md`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_final_embedding_repair_report.md)).
- **Raw Data Artifacts Generated**:
  - [`benchmark/results/qwen_43_embedding_verification.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_embedding_verification.json)
  - [`benchmark/results/qwen_embedding_repair_raw_excerpt.txt`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_embedding_repair_raw_excerpt.txt)

---

## 4. Gold-Cross-Reference for 9 Affected Questions

Cross-referencing the 43 historically missing chunks against the 100 benchmark questions revealed **exactly 9 benchmark questions** whose gold documents overlapped with the affected chunk set:

| QID | Question Type | Historically Affected Chunk ID | Tool Used | Tool Result | Norm Match | Gold Evidence Hit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pub-001` | Aggregation | `Q47155555_chunk_1` | `graphrag__aggregate` | SUCCESS | `True` | `True` |
| `pub-021` | Superlative | `Q1222641_chunk_0` | `graphrag__superlative` | SUCCESS | `True` | `True` |
| `pub-024` | Aggregation | `Q280553_chunk_0` | `graphrag__aggregate` | SUCCESS | `True` | `True` |
| `pub-045` | Aggregation | `Q2463752_chunk_4` | `graphrag__aggregate` | SUCCESS | `True` | `True` |
| `pub-053` | Superlative | `Q26228283_chunk_0` | `graphrag__superlative` | SUCCESS | `True` | `True` |
| `pub-058` | Aggregation | `Q17515790_chunk_0` | `graphrag__aggregate` | SUCCESS | `True` | `True` |
| `pub-066` | Superlative | `Q7979972_chunk_0`, `Q7979977_chunk_1` | `graphrag__superlative` | SUCCESS | `True` | `True` |
| `pub-078` | Aggregation | `Q26860_chunk_1` | `graphrag__aggregate` | SUCCESS | `True` | `True` |
| `pub-087` | Aggregation | `Q3628683_chunk_5` | `graphrag__aggregate` | SUCCESS | `True` | `True` |

### Key Finding:
All 9 affected questions were structured questions (Aggregation / Superlative) routed dynamically to Phase 6 deterministic GSQL tools (`graphrag__aggregate` or `graphrag__superlative`). Consequently, all 9 queries achieved **100% normalized match** and **100% gold evidence hit rate** directly via structured graph traversal, incurring **zero negative impact** from vector embedding state during Phase 7 execution.

- **Raw Data Artifacts Generated**:
  - [`benchmark/results/qwen_43_gold_cross_reference.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_gold_cross_reference.csv)
  - [`benchmark/results/qwen_43_gold_cross_reference.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_gold_cross_reference.json)

---

## 5. Phase 3 Aggregation Integrity Verification

Raw analysis of `benchmark/results/phase3_qwen_100_benchmark.jsonl` for the 21 aggregation questions verified:

- **Strict Exact Match**: **0 / 21 (0.0%)**
- **Normalized Substring Match**: **18 / 21 (85.71%)**
- **Gold Document Retrieval Hit**: **0 / 21 (0.0%)**
- **Combined Evidence Hit**: **0 / 21 (0.0%)**

### Diagnostic Implication:
This historical baseline result represents an **"answer-string match without verified gold-document retrieval"**. The evaluator allowed LLM parametric memory or coincidental number generation to match the ground truth string even though zero gold text chunks were retrieved by vector search.

- **Raw Data Artifact Generated**:
  - [`benchmark/results/phase3_aggregation_integrity.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/phase3_aggregation_integrity.csv)

---

## 6. Current Embedding State Verification

- **Total `DocumentChunk` Vertices**: 5,716
- **`qwen_embedding` Non-Null Count**: 5,716 (100.0%)
- **`qwen_embedding` Null Count**: 0
- **Vector Dimension**: 1,024-d
- **Verification Source**: `benchmark/results/qwen_final_embedding_repair_report.md` & `scratch/audit_chunk_discrepancy_report.json`

---

## 7. Recomputed Evidence Metric Cross-Check

Independently calculated from `benchmark/results/agentic_full_100_evidence_recomputed.jsonl`:

- **Total Questions Attempted**: 100
- **Completed Questions**: 94 (6 HTTP timeouts)
- **Overall Normalized Answer Accuracy**: **87 / 100 = 87.0%**
- **Combined Gold Evidence Hit Rate (All 100)**: **93 / 100 = 93.0%**
- **Combined Gold Evidence Hit Rate (Completed 94)**: **93 / 94 = 98.94%**

### Breakdown by Question Type:

1. **Aggregation** (21 questions):
   - Normalized Accuracy: **21 / 21 (100.0%)**
   - Combined Evidence Hit Rate: **21 / 21 (100.0%)**
2. **Lookup** (19 questions):
   - Normalized Accuracy: **19 / 19 (100.0%)**
   - Combined Evidence Hit Rate: **19 / 19 (100.0%)**
3. **Temporal** (22 questions):
   - Normalized Accuracy: **21 / 22 (95.45%)**
   - Combined Evidence Hit Rate: **21 / 22 (95.45%)**
4. **Superlative** (10 questions):
   - Normalized Accuracy: **8 / 10 (80.0%)**
   - Combined Evidence Hit Rate: **10 / 10 (100.0%)**
5. **Multi-Hop** (28 questions):
   - Normalized Accuracy: **18 / 28 (64.29%)**
   - Combined Evidence Hit Rate: **22 / 28 (78.57%)**
   - Gold Chunk Hit Rate: **21 / 27 (77.78%)**
6. **Retrieval Intrusion**:
   - **0.00% across 22 computable text-retrieval cases; 78 cases were N/A** (structured tools return deterministic subgraphs, making intrusion N/A).

---

## 8. Timeout Verification (6 Questions)

The 6 HTTP 120-second timeout questions were verified directly from raw JSONL exception records:

1. `pub-013` (Temporal): *"Who won the gold medal in the women's 200 metre freestyle swimming event at the Summer Olympics held immediately before 2016?"*
2. `pub-015` (Multi-Hop): *"Who won the gold medal in the event held at London Velopark on 3 to 4 August at the 2012 Summer Olympics?"*
3. `pub-076` (Multi-Hop): *"Who won the gold medal in the event held at Sestriere on February 24, 2006?"*
4. `pub-077` (Multi-Hop): *"Who won the gold medal in the event held at Xiaohaituo Bobsleigh and Luge TrackBeijing on 13, 14 February 2022?"*
5. `pub-096` (Multi-Hop): *"Who won the gold medal in the event held at Riocentro – Pavilion 6 on 10–21 August 2016?"*
6. `pub-098` (Multi-Hop): *"Who won the gold medal in the event held at Sydney Convention and Exhibition Centre on 18 September to 1 October 2000?"*

- **Distribution**: Temporal = 1 (`pub-013`), Multi-Hop = 5 (`pub-015`, `pub-076`, `pub-077`, `pub-096`, `pub-098`).

---

## 9. Master Documentation Inventory

All raw verification artifacts are saved and accessible:
- [`benchmark/results/multihop_joint_integrity_table.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/multihop_joint_integrity_table.csv)
- [`benchmark/results/multihop_joint_integrity_table.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/multihop_joint_integrity_table.json)
- [`benchmark/results/qwen_43_embedding_verification.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_embedding_verification.json)
- [`benchmark/results/qwen_43_gold_cross_reference.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_gold_cross_reference.csv)
- [`benchmark/results/qwen_43_gold_cross_reference.json`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_43_gold_cross_reference.json)
- [`benchmark/results/phase3_aggregation_integrity.csv`](file:///d:/Hackathons/TigerGraph/benchmark/results/phase3_aggregation_integrity.csv)
- [`benchmark/results/qwen_embedding_repair_raw_excerpt.txt`](file:///d:/Hackathons/TigerGraph/benchmark/results/qwen_embedding_repair_raw_excerpt.txt)
- [`scratch/verify_final_integrity_readonly.py`](file:///d:/Hackathons/TigerGraph/scratch/verify_final_integrity_readonly.py)
- [`docs/MASTER_PROJECT_HISTORY.md`](file:///d:/Hackathons/TigerGraph/docs/MASTER_PROJECT_HISTORY.md)
