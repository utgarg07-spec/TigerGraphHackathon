# PHASE 11B — Gate 6 Baseline Snapshot

**Date**: 2026-09-29  
**Status**: GATE 6A BASELINE RECORDED

---

## 1. Git Status & Modified Files

Pre-existing modified files in repository working tree:
- `benchmark/runner.py`
- `common/embeddings/embedding_services.py`
- `common/embeddings/tigergraph_embedding_store.py`
- `common/llm_services/base_llm.py`
- `common/llm_services/groq_llm_service.py`
- `common/llm_services/ollama.py`
- `common/py_schemas/schemas.py`
- `configs/server_config.json`
- `graphrag/app/agent/agent_graph.py`
- `graphrag/app/agent/agentic_executor.py`
- `graphrag/app/agent/agentic_graph.py`
- `graphrag/app/agent/agentic_planner.py`
- `graphrag/app/supportai/retrievers/HybridRetriever.py`
- `graphrag/app/supportai/retrievers/SimilarityRetriever.py`
- `graphrag/app/tools/generate_cypher.py`
- `graphrag/app/tools/graphrag_tools.py`
- `graphrag/app/tools/olympic_tools.py`
- `graphrag/app/tools/test_olympic_tools.py`
- `graphrag/app/tools/tool_registry.py`

---

## 2. Phase 6 Tool Suite Verification

- **Command**: `docker exec graphrag python /code/tools/test_olympic_tools.py`
- **Result**: **78 / 78 PASS (100.0%)**
  - Tool 1 (`graphrag__lookup`): 19/19 PASS
  - Tool 2 (`graphrag__aggregate`): 21/21 PASS
  - Tool 3 (`graphrag__superlative`): 10/10 PASS
  - Tool 4 (`graphrag__temporal_resolve`): 22/22 PASS
  - Edge Cases: 6/6 PASS

---

## 3. Current Phase 11 Baseline Accuracy by QType

| Question Type | Count | Baseline Correct | Baseline Accuracy | Notes |
|:---|:---:|:---:|:---:|:---|
| **Lookup** | 19 | 19 | 100.0% | Stable deterministic routing |
| **Temporal** | 22 | 21 | 95.45% | 1 timeout (`pub-013`) |
| **Aggregation** | 21 | 21 | 100.0% | 100% verified analytical query execution |
| **Superlative** | 10 | 8 | 80.00% | 2 synthesis title shortening (`pub-004`, `pub-008`) |
| **Multi-Hop** | 28 | 18 | 64.29% | 10 failures |
| **TOTAL** | **100** | **87** | **87.00%** | Combined evidence = 93.0% |

---

## 4. Timeout QID Breakdown (6 Total)

1. `pub-013` (Temporal) — Client HTTP read timeout (120s)
2. `pub-015` (Multi-Hop) — Client HTTP read timeout (120s)
3. `pub-076` (Multi-Hop) — Client HTTP read timeout (120s)
4. `pub-077` (Multi-Hop) — Client HTTP read timeout (120s)
5. `pub-096` (Multi-Hop) — Client HTTP read timeout (120s)
6. `pub-098` (Multi-Hop) — Client HTTP read timeout (120s)

---

## 5. Multi-Hop Failure QID Breakdown (10 Total from `PHASE_11A_MULTIHOP_FAILURES.csv`)

| QID | Gold Answer | Previous Category | Root Cause |
|:---|:---|:---|:---|
| `pub-015` | Dani KingLaura TrottJoanna Rowsell | `timeout` / other | Client HTTP timeout (120s) during joint graph-vector search |
| `pub-017` | Yi Siling | `retrieval_miss` | Target shooting event for 28 July 2012 missed in vector top-k |
| `pub-023` | Hwang Young-Cho | `synthesis` | Gold event resolved; synthesizer output boilerplate failure text |
| `pub-060` | Yana Shemyakina | `tool_argument_error` | Schema validation error (empty/missing question arg) exhausted calls |
| `pub-067` | Rosannagh MacLennan | `synthesis` | Gold event resolved; synthesizer output boilerplate failure text |
| `pub-076` | Julia Mancuso | `timeout` / other | Client HTTP timeout (120s) during multi-hop graph traversal |
| `pub-077` | Kaillie Humphries | `timeout` / other | Client HTTP timeout (120s) during multi-hop graph traversal |
| `pub-096` | Fazliddin Gaibnazarov | `timeout` / other | Client HTTP timeout (120s) during multi-hop graph traversal |
| `pub-098` | Bekzat Sattarkhanov | `timeout` / other | Client HTTP timeout (120s) during multi-hop graph traversal |
| `pub-099` | Erik LesserDaniel BöhmArnd PeifferSimon Schempp | `output_formatting` | Extracted all 4 relay team members; gold string was unspaced concatenation |
