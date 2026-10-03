# Phase 5 — Qwen GraphRAG Hybrid Pilot Metric Validation Report

**Date**: September 23, 2026  
**Status**: VALIDATION COMPLETE  
**Target Benchmark**: Phase 5 Qwen GraphRAG Hybrid Pilot (5 Representative Public Questions)  

---

## A. Canonical Gold IDs & Answers

Extracted directly from `data/eval_public.jsonl` without inference:

| QID | Question Type | Canonical Question | Canonical Answer | Canonical `gold_doc_ids` |
|---|---|---|---|---|
| **pub-001** | aggregation | According to the provided corpus, how many biathlon events at the 2018 Winter Olympics had more than 73 competitors? | `['5']` | `['Q47091419', 'Q47105341', 'Q47155365', 'Q47155371', 'Q47155408', 'Q47155425', 'Q47155467', 'Q47155505', 'Q47155541', 'Q47155555', 'Q47155815']` (11 docs) |
| **pub-002** | temporal | Who won the gold medal in the men's 20 kilometres walk athletics event at the Summer Olympics held immediately before 2016? | `['Chen Ding']` | `['Q1050909', 'Q26233122']` (2 docs) |
| **pub-004** | superlative | According to the provided corpus, which athletics event at the 2008 Summer Olympics had the highest number of competitors? | `["Athletics at the 2008 Summer Olympics – Men's marathon"]` | `['Q1005784', 'Q1043342', 'Q1043347', 'Q1043354', 'Q1043361', 'Q1066390', 'Q1084677', 'Q247070', 'Q257545', 'Q288549', 'Q517035', 'Q544177', 'Q656634', 'Q657467', 'Q677027', 'Q693595', 'Q743905', 'Q744487', 'Q754844', 'Q766954', 'Q830711', 'Q847592', 'Q848278', 'Q848291', 'Q853003', 'Q853023', 'Q853040', 'Q853049', 'Q853072', 'Q899312', 'Q903439', 'Q904345', 'Q916976', 'Q917323', 'Q917328', 'Q917333', 'Q917348', 'Q922248', 'Q922361', 'Q932865', 'Q947678', 'Q947691', 'Q947750']` (43 docs) |
| **pub-005** | multi_hop | Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988? | `['Oksen Mirzoyan']` | `['Q25239316']` (1 doc) |
| **pub-009** | lookup | How many nations participated in the 2006 Winter Olympics? | `['80']` | `['Q26254891']` (1 doc) |

---

## B & C. Replay / Pilot Retrieved IDs & Exact Intersection Audit

Evaluated using the mathematical definition:  
$$\text{gold\_doc\_hit} = \text{any}(g \in \text{retrieved\_doc\_ids} \text{ for } g \in \text{canonical\_gold\_doc\_ids})$$

| QID | Question Type | Pilot `retrieved_doc_ids` | Exact Intersection ($g \in \text{retrieved} \cap \text{gold}$) | Canonical Hit Status |
|---|---|---|---|---|
| **pub-001** | aggregation | `['Q1005133', 'Q1222101', 'Q1222187', 'Q47155408', 'Q47155425']` | **`['Q47155408', 'Q47155425']`** (2 hits) | **HIT** |
| **pub-002** | temporal | `['Q26219856', 'Q26233122', 'Q776944', 'Q853023', 'Q936622']` | **`['Q26233122']`** (1 hit) | **HIT** |
| **pub-004** | superlative | `[]` (0 docs retrieved) | `[]` (0 hits) | **MISS** |
| **pub-005** | multi_hop | `['Q25239314', 'Q25239321', 'Q25239533', 'Q269521', 'Q508776']` | `[]` (0 hits) | **MISS** |
| **pub-009** | lookup | `['Q2558792', 'Q2563927', 'Q26250761', 'Q26254891', 'Q3039134']` | **`['Q26254891']`** (1 hit) | **HIT** |

---

## D. Correct 5-Question Recall

- **Total Pilot Questions**: 5
- **Canonical Gold Document Hits**: **3 / 5** (`pub-001`, `pub-002`, `pub-009`)
- **Canonical Gold Document Misses**: **2 / 5** (`pub-004`, `pub-005`)
- **True Gold-Document Recall**: **60.0%**

---

## E. Fallback Implementation Status Audit

Code inspection was conducted on `graphrag/app/supportai/retrievers/HybridRetriever.py`, `graphrag/app/tools/graphrag_tools.py`, and `supportai/retrieval/GSQL_queries/GraphRAG_Hybrid_Qwen_Vector_Search.gsql`.

### Code Audit Findings:
1. **Fallback Implementation**: **NOT IMPLEMENTED**.
   - Neither `HybridRetriever.py` nor `graphrag_tools.py` contains fallback logic to query `Content_Similarity_Qwen_Vector_Search` or union pure vector search results when hybrid traversal returns 0 or fewer than `top_k` results.
2. **Active Code Path Status**: **INACTIVE**.
   - No fallback mechanism exists in the active execution path.
3. **Exercised by `pub-004`?**: **NO**.
   - `pub-004` yielded `"final_retrieval": {}` (0 chunks). Because no fallback was implemented, 0 chunks were passed to answer generation, resulting in 0 retrieved document IDs and `(no answer produced)`.

---

## F. Discrepancy Analysis: Previous Report vs. Canonical Data

The previous report (`benchmark/results/phase5_qwen_hybrid_pilot_report.md`) contained document ID citations in its text table that differed from the true intersecting canonical `gold_doc_ids`:

1. **`pub-001` (aggregation)**:
   - *Previous Report Table Cited*: `Q1222187` (1998 Winter Olympics biathlon document).
   - *Canonical Reality*: `Q1222187` is NOT a gold document for 2018 biathlon events. The actual intersecting gold documents retrieved were **`Q47155408`** (2018 Men's 20 km individual, 86 competitors) and **`Q47155425`** (2018 Women's 15 km individual, 87 competitors). The hit label (**HIT**) was correct, but the cited document ID in the prose table was incorrect.

2. **`pub-002` (temporal)**:
   - *Previous Report Table Cited*: `Q853023` (2008 Summer Olympics Men's 20km walk).
   - *Canonical Reality*: `Q853023` is NOT in canonical `gold_doc_ids`. The actual intersecting gold document retrieved was **`Q26233122`** (2016 Men's 20km walk, which contains background info on 2012 champion Chen Ding). The hit label (**HIT**) was correct, but the cited document ID in the prose table was incorrect.

3. **`pub-004` (superlative)**:
   - *Previous Report Table Cited*: `Q18640776`.
   - *Canonical Reality*: `Q18640776` is NOT in canonical `gold_doc_ids` (which contains 43 2008 athletics event documents). The actual result was 0 retrieved document IDs (**MISS**).

4. **`pub-005` (multi_hop)**:
   - *Previous Report Table Cited*: `Q508776` ("partial match / gold target Q25239314").
   - *Canonical Reality*: The canonical gold document is **`Q25239316`** (Men's 56kg weightlifting on 20 September 1988). The retriever retrieved neighboring weightlifting categories (`Q25239314` - 52kg, `Q25239321` - 60kg, `Q25239533` - 75kg), missing `Q25239316`. The true status is **MISS**.

5. **`pub-009` (lookup)**:
   - *Previous Report Table Cited*: `Q2558792`.
   - *Canonical Reality*: `Q2558792` is 1994 Winter Olympics. The actual intersecting gold document retrieved was **`Q26254891`** (2006 Winter Olympics main page). The hit label (**HIT**) was correct, and `Q26254891` was indeed in the retrieved set.

### Summary of Discrepancies
- **True Gold-Document Recall Score**: **60.0% (3/5)**. (The aggregate 3/5 score in the previous report was numerically correct, but the document IDs cited in the text table were erroneous).
- **Fallback Mitigation Claim**: Unimplemented in code.
