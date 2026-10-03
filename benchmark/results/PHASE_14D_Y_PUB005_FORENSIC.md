# PHASE 14D-Y — PUB-005 PLANNING/DISAMBIGUATION FORENSIC AUDIT REPORT

## Executive Summary

Phase 14D-Y conducted an offline forensic analysis of `pub-005` ("Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?") to determine whether a code change or planner modification is warranted.

### Final Audit Status: `NO_CODE_FIX_JUSTIFIED`

- **Planner Behavior**: The planner's decision to route `pub-005` to `graphrag__hybrid_search` is **correct**. Venue names (`"Olympic Weightlifting Gymnasium"`) and exact dates (`"20 September 1988"`) are natural-language text metadata, not normalized graph attributes.
- **Retrieval Performance**: `graphrag__hybrid_search` succeeded **100%** by retrieving the exact gold document (`q25239316_chunk_0`, gold answer: `Naim Süleymanoğlu`).
- **No Code Fix Justified**: Neither a planner code modification nor a tool contract change is justified. The retrieval layer contract and agentic executor are working as designed.

---

## Y1 — Reconstruction of `pub-005` Planner Decision

1. **Question Text**: `"Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?"`
2. **QType**: `multi_hop` | **Gold Document**: `["Q25239316"]` | **Gold Answer**: `["Naim Süleymanoğlu"]`.
3. **Plan Generated**:
   ```python
   Plan(steps=[
       PlanStep(id="S1", kind="unstructured", tool="graphrag__hybrid_search", args={"question": "gold medal winner event held at Olympic Weightlifting Gymnasium on 20 September 1988", "top_k": 5}),
       PlanStep(id="A", kind="answer", tool="", depends_on=["S1"])
   ])
   ```
4. **Why `hybrid_search` Was Selected**:
   - `agentic_planner.py` system prompt contains explicit guidance:
     *"If a question identifies an event or topic using textual venue names, sub-venues, specific dates, date ranges... prefer graphrag__hybrid_search over graphrag__structural_retrieve."*
   - Deterministic tools (`lookup`, `aggregate`, `superlative`, `temporal_resolve`) require normalized sport/games/event_title entity names. None accept venue or date strings.
   - Upfront before retrieval, the planner cannot know the canonical event title (`"Weightlifting at the 1988 Summer Olympics – Men's 60 kg"`). Therefore `graphrag__hybrid_search` is the **only valid first step**.

---

## Y2 — Evidence Analysis

`graphrag__hybrid_search` returned 5 chunks in `S1.context`, including:

- **Gold Document Chunk (`q25239316_chunk_0`)**:
  - `event`: Men's 60 kg weightlifting
  - `games`: 1988 Summer Olympics
  - `venue`: Olympic Weightlifting Gymnasium
  - `date`: **20 September 1988**
  - `gold`: **Naim Süleymanoğlu** (TUR)
- **Competing Document Chunk (`Q25239533_chunk_0`)**:
  - `event`: Men's 67.5 kg weightlifting
  - `games`: 1988 Summer Olympics
  - `venue`: Olympic Weightlifting Gymnasium
  - `date`: 21 September 1988 (Infobox), body text states competition took place on 20 September.
  - `gold`: Joachim Kunz (GDR)

### Operational Finding:
Hybrid retrieval fetched the exact gold document (`Q25239316`) into top-k context. The variation in answer prediction between runs (Naim Süleymanoğlu vs Joachim Kunz) is an LLM synthesis choice between two candidate event chunks present in the retrieved context, **not a planner or retrieval defect**.

---

## Y3 — Architectural Classification

- **Intended Architecture**: **Option A (Hybrid Retrieval Only)**.
- **Justification**: Questions containing text metadata (venues, dates) are designed to be answered via text vector search (`graphrag__hybrid_search`). Hybrid search successfully retrieved the target document. No secondary structural query is supported by schema for venue/date strings.

---

## Y4 — Minimum Legitimate Fix Determination

- **Planner Code Fix Justified**: **NO**.
- **Executor Code Fix Justified**: **NO**.
- **Tool Contract Fix Justified**: **NO**.
- **Conclusion**: **`NO_CODE_FIX_JUSTIFIED`**. The pipeline contracts are healthy and verified.

---

## Y5 — Regression Safety Confirmation

- **Phase 6**: Untouched.
- **Phase 12/13**: Untouched.
- **Fix A Line 863 (`base_llm.py`)**: Untouched & Live-Verified.
- **Fix B (`agentic_executor.py`)**: Untouched.
- **Retrieval / GSQL / Embeddings**: Untouched.
- **Evaluator**: Untouched.

---

## Verification & Constraints Checklist

- **Production Modifications during Audit**: `0`
- **AIRouter API Calls**: `0`
- **Live Questions Executed**: `0`
