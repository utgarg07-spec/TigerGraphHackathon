# Agentic GraphRAG — TigerGraph Hackathon 2026

> A production-oriented Agentic GraphRAG system built on TigerGraph that combines graph retrieval, vector retrieval, deterministic tools, planning, evidence evaluation, and grounded synthesis.

## Results at a Glance

The same **100-question public benchmark** was evaluated across three pipelines using the project's unified evaluation contract.

| Metric | Classical RAG | GraphRAG | **Agentic GraphRAG** |
|---|---:|---:|---:|
| Questions | 100 | 100 | **100** |
| Accuracy | 19/100 (19.0%) | 20/100 (20.0%) | **95/100 (95.0%)** |
| HTTP Success | 100/100 (100%) | 100/100 (100%) | **100/100 (100%)** |
| Evidence / Gold Recall | 3/100 (3.0%) | 16/100 (16.0%) | **95/100 (95.0%)** |
| Mean Latency | 11.29 s | 35.04 s | **39.43 s** |
| Total Runtime | ~18.8 min | ~58.4 min | **~65.7 min** |
| Average LLM Calls / Question | 1.00 | 1.00 | **3.04** |

### Agentic GraphRAG benchmark highlights

- **95/100** normalized accuracy.
- **72/72 (100%)** across Lookup, Temporal, Aggregation, and Superlative questions.
- **23/28 (82.1%)** on Multi-Hop questions.
- **95/100** gold-evidence recall.
- **100/100** HTTP success.
- **+76 percentage points** over Classical RAG: 19% → 95%.
- **+75 percentage points** over GraphRAG: 20% → 95%.
- Final Phase 15 improvement: **88% → 95% (+7 pp)**.

---

## 1. What We Built

The project implements and evaluates three progressively capable retrieval paradigms over the same TigerGraph-backed dataset.

### Pipeline 1 — Classical RAG

```text
Question → Embedding / Similarity Search → Relevant Chunks → LLM → Answer
```

### Pipeline 2 — GraphRAG

```text
Question → Vector Seed Retrieval → TigerGraph Entity/Relationship Expansion
         → Graph + Document Context → LLM → Answer
```

### Pipeline 3 — Agentic GraphRAG

```text
Question
   ↓
Agentic Triage
   ↓
Planner / Agent
   ↓
Tool Selection
   ├── Deterministic GSQL tools
   ├── Hybrid vector + graph retrieval
   └── Other retrieval tools
   ↓
Evidence Evaluation
   ↓
Replan when required
   ↓
Grounded Synthesis
   ↓
Final Answer
```

The key difference is that retrieval is **not a single fixed sequence**. The agent can select retrieval methods based on the question and evidence returned by previous steps.

---

## 2. Why Agentic GraphRAG?

Simple questions often do not require an agent. A lookup, aggregation, or temporal question can frequently be answered with a deterministic graph operation.

More complex questions may require connecting multiple entities, traversing relationships, retrieving supporting documents, or changing retrieval strategy after an intermediate result.

The system therefore combines:

- **Deterministic retrieval** for reliable graph/database operations.
- **Hybrid retrieval** using vector similarity and graph context.
- **Agentic planning** to decide which retrieval operations are needed.
- **Evidence evaluation** to determine whether sufficient evidence exists.
- **Bounded replanning** for additional investigation without infinite execution.
- **Grounded synthesis** from retrieved evidence.

---

## 3. System Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         User / Chat UI                           │
└───────────────────────────────┬──────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                           │
│  Chat API • Agentic Engine • Benchmark APIs • Trace APIs         │
└───────────────────────────────┬──────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                         Agentic Layer                             │
│  Triage → Planner → Tool Selection → Evidence → Replan → Answer │
└──────────────┬───────────────────────┬───────────────────────────┘
               │                       │
               ↓                       ↓
┌─────────────────────────┐   ┌───────────────────────────────────┐
│ Deterministic Tools     │   │ Hybrid GraphRAG Retrieval         │
│                         │   │                                   │
│ Olympic GSQL queries    │   │ Qwen embeddings                   │
│ Lookup / temporal       │   │ Vector retrieval                  │
│ Aggregation             │   │ TigerGraph traversal              │
│ Superlative             │   │ Document chunks                   │
└────────────┬────────────┘   └────────────────┬──────────────────┘
             │                                  │
             └────────────────┬─────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │     TigerGraph      │
                    │  Graph + Vector DB  │
                    └─────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ Evidence / Context  │
                    └─────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ AIRouter / GPT-OSS  │
                    │   openai/gpt-oss-20b│
                    └─────────────────────┘
```

### Main production components

| Component | Role |
|---|---|
| TigerGraph | Graph database, graph traversal, structured retrieval |
| Qwen3 embedding model | Document/chunk vector embeddings |
| AIRouter | OpenAI-compatible LLM endpoint |
| `openai/gpt-oss-20b` | Agent planning and synthesis |
| MCP / deterministic tools | Structured graph operations |
| FastAPI | Backend and benchmark/UI APIs |
| React + TypeScript | Interactive dashboard and chat UI |
| Unified evaluator | Reproducible benchmark evaluation |

---

## 4. Agentic Execution

Execution is deliberately bounded to prevent uncontrolled retries and infinite planning loops.

```text
MAX_LLM_CALLS          = 6 per question
MAX_REPLANS            = 1
MAX_AGENT_STEPS        = 5
MAX_PROVIDER_ATTEMPTS  = 2
ChatOpenAI(max_retries=0)
```

### Planned style

```text
Question → Plan retrieval DAG → Execute tools → Evaluate evidence
         → Replan if necessary → Synthesize
```

### Reactive style

```text
Question → Action → Observe → Choose next action → Observe → ... → Answer
```

The UI exposes Agent modes including Auto, Planned, and Reactive where supported by the configured model/tool capabilities.

---

## 5. Benchmark

### Dataset

The public benchmark contains **100 questions**:

```text
data/eval_public.jsonl
```

SHA-256:

```text
ABDDB7D18A6D8ED908F514A7E560FE4950EBE479EBB2CDB75A7456887C10C6E5
```

The hidden evaluation set is intentionally **not included** in the public repository.

### Evaluation contract

The unified evaluator measures:

- Normalized accuracy
- HTTP success
- Evidence / gold recall
- Latency
- Token usage
- LLM calls
- Retrieval/tool behavior
- Per-question results and traces

### Final three-way comparison

| Metric | RAG | GraphRAG | Agentic GraphRAG |
|---|---:|---:|---:|
| Accuracy | **19%** | **20%** | **95%** |
| Evidence Recall | 3% | 16% | **95%** |
| HTTP Success | 100% | 100% | **100%** |
| Avg Latency | 11.29 s | 35.04 s | 39.43 s |
| Avg LLM Calls | 1.00 | 1.00 | **3.04** |
| Total Runtime | ~1,128.9 s | ~3,504.3 s | **3,943.0 s** |

### By question type

| Question Type | Result |
|---|---:|
| Aggregation | **21/21 (100%)** |
| Lookup | **19/19 (100%)** |
| Temporal | **22/22 (100%)** |
| Superlative | **10/10 (100%)** |
| Multi-Hop | **23/28 (82.1%)** |
| **Overall** | **95/100 (95%)** |

The remaining five failures were retained rather than hidden or excluded from the final benchmark.

---

## 6. Benchmark Dashboard

The repository includes an interactive benchmark dashboard for exploring the evaluation rather than relying only on static tables.

### Dashboard sections

- **Overview**
- **System Evolution**
- **Benchmark**
- **Evidence / Logs**
- **Technical / Provenance**

Read-only benchmark endpoints include:

```text
/ui/benchmark/overview
/ui/benchmark/comparison
/ui/benchmark/questions
/ui/benchmark/questions/{qid}
/ui/benchmark/failures
/ui/benchmark/provenance
/ui/benchmark/evolution
```

The question explorer supports PASS/FAIL filtering and individual question drilldown.

---

## 7. Evidence and Provenance

Important benchmark artifacts are retained in the repository:

```text
data/eval_public.jsonl

benchmark/results/
├── rag_baseline_summary.json
├── graphrag_baseline_summary.json
├── three_way_comparison.json
├── FINAL_100Q_AGENTIC_BENCHMARK_SUMMARY.json
├── FINAL_100Q_AGENTIC_BENCHMARK_REPORT.md
├── FINAL_100Q_AGENTIC_BENCHMARK.jsonl
└── FINAL_100Q_AGENTIC_QID_TRACE.csv

benchmark/
└── unified_evaluator.py
```

Phase reports, benchmark traces, tests, and implementation notes are also retained to make the development history auditable.

---

## 8. Final Failure Analysis

The final **95/100** result was not obtained by removing difficult questions. Five questions remained unsuccessful in the final benchmark.

The retained failure categories were:

1. Structural tool routing on natural-language venue/date queries.
2. Hybrid vector top-k retrieval misses.
3. Underspecified multi-candidate venue/date queries.
4. An evaluator/benchmark label artifact.
5. Replan budget exhaustion.

These limitations are retained as part of the final benchmark record.

---

## 9. Reliability Engineering

The final implementation includes bounded execution and provider handling:

- Provider retries are bounded.
- LLM calls are budgeted per question.
- Planner retries are bounded.
- Agent steps are bounded.
- HTTP 429 handling is bounded.
- Function-call error envelopes are handled.
- Adapter extraction was fixed for provider responses.
- DAG argument type protection prevents incompatible tool arguments.
- Deterministic tool regression coverage is retained.

The deterministic Olympic tool layer passed:

```text
78 / 78 tests
```

---

## 10. Model and Retrieval Configuration

### Completion model

```text
Provider: AIRouter
Model: openai/gpt-oss-20b
Temperature: 0
Reasoning effort: low
```

### Embeddings

```text
Model: qwen3-embedding:0.6b
Dimensions: 1024
```

### Retrieval

The system uses TigerGraph for structured graph retrieval and hybrid retrieval, with deterministic GSQL tools for known question classes and vector retrieval for document-level evidence.

Production credentials are intentionally excluded from version control. Use the provided configuration template and environment variables for local setup.

---

## 11. Repository Structure

```text
.
├── benchmark/                 # Evaluation and benchmark runners
├── common/                    # Shared LLM, prompts, tools, utilities
├── configs/                   # Configuration templates
├── data/                      # Public benchmark and corpus data
├── docs/                      # Reports, diagrams, phase documentation
├── graph/                     # TigerGraph schema / graph artifacts
├── graphrag/                  # GraphRAG backend
├── graphrag-ui/               # React frontend and benchmark dashboard
├── ecc/                       # Knowledge graph construction service
├── chat-history/              # Chat history service
├── tests/                     # Tests
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## 12. Quick Start

### Prerequisites

- Docker / Docker Compose
- Python environment as required by the backend
- TigerGraph instance
- LLM provider API access
- Required embedding model
- Node.js / pnpm for frontend development

### Configuration

Do **not** commit production credentials.

Start from:

```text
configs/server_config.example.json
```

and provide credentials through your local configuration/environment.

The production configuration used for the benchmark is excluded from version control.

### Backend

The backend is exposed through the project's FastAPI application.

### Frontend

The dashboard is located at:

```text
graphrag-ui/
```

The Vite development server proxies `/ui` requests to the backend.

For the complete deployment topology, use the repository's Docker Compose configuration and project documentation.

---

## 13. Dashboard and Chat

### Agentic Chat

Used to demonstrate:

- Natural-language questions
- Agent planning
- Tool selection
- Graph retrieval
- Evidence collection
- Grounded synthesis
- Trace inspection

### Benchmark Dashboard

Used to demonstrate:

- Three-way pipeline comparison
- Accuracy
- Evidence recall
- Latency
- Token / LLM-call behavior
- Question-level results
- Failure analysis
- Benchmark provenance

---

## 14. Development History

The project was developed incrementally through benchmark-driven phases, including:

- Initial RAG baseline
- GraphRAG baseline
- Hybrid retrieval experiments
- Deterministic tool layer
- Agentic planning
- Provider adapter fixes
- Tool-routing tests
- Local-model experiments
- Reliability and budget controls
- Agentic benchmark iterations
- Final Phase 15 benchmark
- Dashboard implementation
- Submission/security hardening

The detailed phase artifacts remain in `docs/`, `benchmark/`, and related directories.

---

## 15. Limitations

Agentic GraphRAG improves answer accuracy in the final benchmark, but it also incurs greater latency and more LLM calls than the simpler baselines.

```text
RAG:
  19% accuracy
  11.29 s mean latency
  1.00 LLM call/question

GraphRAG:
  20% accuracy
  35.04 s mean latency
  1.00 LLM call/question

Agentic GraphRAG:
  95% accuracy
  39.43 s mean latency
  3.04 LLM calls/question
```

This trade-off is part of the evaluation rather than being hidden.

---

## 16. Original TigerGraph GraphRAG Project

This submission builds on the TigerGraph GraphRAG project.

The upstream GraphRAG documentation, deployment material, provider configuration examples, and original project assets remain available throughout this repository and its `docs/` directory.

Upstream project:

https://github.com/tigergraph/graphrag

The current upstream GraphRAG release line uses the **AGPL-3.0** license. See [LICENSE](./LICENSE) for the repository license text.

---

## 17. Hackathon Submission

### Round 1 deliverables

- [x] Working Agentic GraphRAG system
- [x] Public GitHub repository
- [x] Architecture
- [x] Three-way benchmark
- [x] Metrics dashboard
- [ ] Demo video — **add final link here**

### Core result

```text
CLASSICAL RAG       19%
GRAPH RAG           20%
AGENTIC GRAPHRAG    95%
```

**100 questions. 100% HTTP completion. 95% normalized accuracy. 95% gold-evidence recall. 23/28 multi-hop questions.**

---

## 18. License

This repository retains the upstream TigerGraph GraphRAG licensing terms.

See [LICENSE](./LICENSE) for the full license text.
