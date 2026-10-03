# Unified Three-Way Evaluation Specification & Contract

**Document Version**: 1.0.0 (Authoritative Evaluation Contract)  
**Date**: September 28, 2026  
**Target Systems**: RAG (Phase 3), GraphRAG (Phase 5), Agentic GraphRAG (Phase 7/10)  
**Implementation**: `benchmark/evaluation_contract.py` & `benchmark/unified_evaluator.py`

---

## 1. Executive Summary & Purpose

This document establishes a **Unified Three-Way Evaluation Contract** capable of evaluating and comparing:
1. **Classic Dense-Vector RAG** (Phase 3 Baseline)
2. **Hybrid GraphRAG** (Phase 5 Baseline)
3. **Agentic GraphRAG** (Phase 7 / Phase 10 Baseline)

The contract enforces strict metric reproducibility, explicit N/A (null) representation for non-applicable features, and deterministic mathematical definitions for all evaluation dimensions without relying on subjective LLM judges.

---

## 2. Field-Availability Matrix

Not every pipeline exposes the same telemetry or tool-calling data. Unavailable metrics MUST be explicitly set to `null` (N/A). Never fabricate values.

| Evaluation Metric / Field | Classic RAG (Phase 3) | Hybrid GraphRAG (Phase 5) | Agentic GraphRAG (Phase 7/10) |
| :--- | :--- | :--- | :--- |
| `qid` | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| `qtype` | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| `prediction` | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| `gold` | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| **A. Correctness** (`normalized_match`) | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| **B. Completeness** (Token Overlap) | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| **C. Grounding** (Context Ratio) | **AVAILABLE** | **AVAILABLE** (N/A on 0-context) | **AVAILABLE** (N/A on GSQL tools) |
| **D. Combined Evidence** (`gold_doc_hit`) | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| **E. Token Efficiency** (`total_tokens`) | **N/A** (None) | **N/A** (None) | **AVAILABLE** |
| **F. Latency** (`latency_ms`) | **AVAILABLE** | **AVAILABLE** | **AVAILABLE** |
| **G. Retrieval Intrusion** (% Distractors) | **AVAILABLE** | **AVAILABLE** (N/A on 0-context) | **AVAILABLE** (N/A on GSQL tools) |
| **H. Agentic Effectiveness** (Tools/Steps) | **N/A** (`steps=1`) | **N/A** (`steps=1`) | **AVAILABLE** |

---

## 3. Canonical Record Schema

Every evaluation record MUST conform to the typed `CanonicalEvaluationRecord` schema (`benchmark/evaluation_contract.py`):

```json
{
  "qid": "pub-001",
  "qtype": "aggregation",
  "prediction": "5",
  "gold": "5",
  "correctness": true,
  "completeness": 1.0,
  "grounding": null,
  "total_tokens": 450,
  "input_tokens": 350,
  "output_tokens": 100,
  "latency_ms": 4960.0,
  "evidence": {
    "gold_chunk_hit": false,
    "gold_vertex_hit": true,
    "gold_tool_evidence_hit": true,
    "cited_gold_hit": false,
    "gold_combined_hit": true,
    "retrieval_intrusion_pct": null
  },
  "citations": [],
  "retrieval_methods": ["graphrag__aggregate"],
  "retrieval_steps": 1,
  "tools": ["graphrag__aggregate"],
  "specialist_agents": ["planner", "executor", "synthesizer"],
  "strategy_changes": 0,
  "stop_reason": "completed"
}
```

---

## 4. Deterministic Metric Definitions (A–H)

### A. Correctness (`normalized_match`)
- **Definition**: Boolean exact or normalized substring match between generated natural language prediction and gold reference.
- **Formula**:
  $$\text{Correctness} = (\text{normalize}(\text{gold}) \in \text{normalize}(\text{pred})) \lor (\text{normalize}(\text{pred}) \in \text{normalize}(\text{gold}))$$
- **Normalization**: Lowercase, strip punctuation, remove articles (`a`, `an`, `the`), fix whitespace. Empty strings evaluate to `False`.

### B. Completeness (Deterministic Word-Overlap Ratio)
- **Definition**: Reproducible percentage of gold answer tokens present in the generated prediction string.
- **Formula**:
  $$\text{Completeness} = \frac{\sum_{t \in \text{tokens}(\text{gold})} \mathbb{I}(t \in \text{pred})}{|\text{tokens}(\text{gold})|}$$

### C. Grounding (Context Token Groundedness)
- **Definition**: Percentage of non-trivial prediction tokens grounded in retrieved context passages.
- **Representation**: `float` $\in [0.0, 1.0]$ when text context is present; `null` (N/A) when structured tools or 0-context queries avoid text retrieval.

### D. Combined Evidence (`gold_combined_hit`)
- **Definition**: Boolean indicator evaluating whether the pipeline retrieved authoritative gold evidence.
- **Components**:
  $$\text{CombinedEvidence} = \text{gold\_chunk\_hit} \lor \text{gold\_vertex\_hit} \lor \text{gold\_tool\_evidence\_hit}$$

### E. Token Efficiency
- **Definition**: Token consumption metrics (`total_tokens`, `input_tokens`, `output_tokens`) and efficiency ratio ($\text{tokens} / \text{correctness}$). Set to `null` if LLM gateway telemetry is absent.

### F. Latency (`latency_ms`)
- **Definition**: Total execution wall-clock duration measured in milliseconds ($\text{latency\_s} \times 1000$).

### G. Retrieval Intrusion (% Distractor Chunks)
- **Definition**: Percentage of retrieved text chunks that are irrelevant distractors.
- **Formula**:
  $$\text{Intrusion} = \frac{|\text{RetrievedChunks} \setminus \text{GoldChunks}|}{|\text{RetrievedChunks}|} \times 100\%$$
- **Rule**: Evaluates to `0.00%` when all chunks are gold; `null` (N/A) when zero text chunks are retrieved.

### H. Agentic Effectiveness
- **Definition**: Telemetry capturing tool choice (`tools`), multi-step planning depth (`retrieval_steps`), replanning loops (`strategy_changes`), and termination status (`stop_reason`).

---

## 5. Offline Testing & Verification

The specification includes 8 offline test cases (`benchmark/test_unified_evaluator.py`):
1. **Exact correct answer**
2. **Incorrect answer**
3. **Evidence hit**
4. **Evidence miss**
5. **N/A metric handling** (explicit `null` representation)
6. **Timeout case** (`stop_reason="timeout"`)
7. **Agentic trace** (multi-step tool execution)
8. **Non-agentic trace** (single-pass vector search)

Run offline tests via:
```bash
python -m unittest benchmark/test_unified_evaluator.py
```
