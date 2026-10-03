# Existing System Archaeology

Based on the repository inspection for Phase 0A, the following details have been verified directly from the code:

## 1. API Route for POST /{graphname}/query
- **File path**: `graphrag/app/routers/inquiryai.py`
- **Function**: `retrieve_answer()` (starts at line 79)
- **Explanation**: This is a FastAPI route `@router.post("/{graphname}/query")` which takes the user's request, connects to the database, creates an agent via `_chat_agent()`, and returns the agent's response.

## 2. Request Model/Schema
- **File path**: `common/py_schemas/schemas.py`
- **Class**: `NaturalLanguageQuery`
- **Explanation**: The route uses `NaturalLanguageQuery` which contains fields like `query`, `mode` (agentic vs classic), `rag_method`, and `include_fields`.

## 3. Key Components Location
- **agentic_planner**: `graphrag/app/agent/agentic_planner.py`
- **agentic_executor**: `graphrag/app/agent/agentic_executor.py`
- **agentic_synthesizer**: `graphrag/app/agent/agentic_synthesizer.py`
- **agentic_react**: `graphrag/app/agent/agentic_react.py`
- **tool_registry**: `graphrag/app/tools/tool_registry.py`
- **main RAG retrieval implementation**: `graphrag/app/agent/agent_graph.py` (contains `TigerGraphAgentGraph` orchestrator logic and `supportai_search` using `supportai.retrievers`)
- **GraphRAG/hybrid retrieval implementation**: `graphrag/app/agent/agent_graph.py` (the `hybrid_search` function) and `supportai.retrievers.HybridRetriever`

## 4. Execution Paths
- **classic + similaritysearch**:
  `agent_graph.py`: `TigerGraphAgentGraph.route_question()` routes to `supportai_lookup` -> `supportai_search()` assigns `method="similaritysearch"` -> dispatches to `similarity_search()` -> results go to `generate_answer()`
- **classic + hybridsearch**:
  `agent_graph.py`: `TigerGraphAgentGraph.route_question()` routes to `supportai_lookup` -> `supportai_search()` assigns `method="hybridsearch"` -> dispatches to `hybrid_search()` -> results go to `generate_answer()`
- **agentic + planned**:
  `agentic_agent.py`: `AgenticAgent.question_for_agent()` calls `_resolve_style()` which returns `"planned"` -> calls `run_agentic()` in `agentic_graph.py` -> explicitly loops through `plan_question()` -> `execute_plan()` -> `synthesize()`
- **agentic + reactive**:
  `agentic_agent.py`: `AgenticAgent.question_for_agent()` calls `_resolve_style()` which returns `"react"` -> calls `run_react()` in `agentic_react.py`

## 5. Agentic Planner Input Location
- **File path**: `graphrag/app/agent/agentic_graph.py` (inside `run_agentic()`)
- **Relevant function**: `plan_question(llm, question, conversation, ctx=ctx)` (from `agentic_planner.py`)
- **Explanation**: The user's question is passed directly into `plan_question()` in `agentic_graph.py` during the initial planning phase (and subsequent replanning phases if needed).

## 6. Existence of `qtype` in /query Request Path
- **Explanation**: A repository-wide regex search for `qtype` yielded 0 results. It currently does not exist anywhere in the `/query` request path, the `NaturalLanguageQuery` schema, or anywhere else.

## 7. Telemetry & Trace Attributes
- **query_sources**: Set as a dictionary on the `GraphRAGResponse` (e.g., `answer.query_sources = {}`), acting as a container for trace data.
- **agent_steps**: Accumulated as a python list of dicts. In classic it's captured over `agent.stream()`. In agentic it's built sequentially in `agentic_graph.py` (capturing `plan`, tool executions, and `synthesize`), then assigned to `query_sources["agent_steps"]`.
- **token usage**: Tracked globally per-request via `start_usage_collection()` and `get_collected_usage()` in `base_llm.py`. It is aggregated (input, output, total, cost) across steps and injected into `query_sources["token_usage"]`.
- **citations**: Built by matching retrieved node keys/IDs with generated answers inside `generate_answer()` or `synthesize()`, then stored in `query_sources["citations"]` and the synthesizer's `agent_steps` output.
- **plan**: Formatted via `[s.model_dump() for s in plan.steps]` and injected as the `output` of the `plan` step within `agent_steps`.

## 8. Official Startup Method
- **File paths**: `README.md` and `docker-compose.yml`
- **Explanation**: The official and primary method for starting the system is via Docker Compose (`docker-compose up`). The `docker-compose.yml` spins up `graphrag`, `graphrag-ecc`, `chat-history`, `graphrag-ui`, and `nginx`.

## Phase 0B: qtype Plumbing Modifications

### Files Modified
- **`common/py_schemas/schemas.py`**: Added `qtype: Optional[str] = None` to `NaturalLanguageQuery`.
- **`graphrag/app/routers/inquiryai.py`**: Updated `retrieve_answer` and `retrieve_answer_with_chathistory` to pass `qtype=query.qtype` to `agent.question_for_agent`.
- **`graphrag/app/agent/agent.py`**: Added `qtype: str = None` parameter to `TigerGraphAgent.question_for_agent()`.
- **`graphrag/app/agent/agentic_agent.py`**: Added `qtype: str = None` parameter to `AgenticAgent.question_for_agent()` and passed it down to `run_agentic`, `run_react`, and the fallback classic `question_for_agent`.
- **`graphrag/app/agent/agentic_graph.py`**: Added `qtype=None` parameter to `run_agentic` and passed it down to `plan_question`.
- **`graphrag/app/agent/agentic_react.py`**: Added `qtype=None` parameter to `run_react` and appended `## Question Type\n{qtype}` to the user prompt if present.
- **`graphrag/app/agent/agentic_planner.py`**: Added `qtype=None` parameter to `plan_question` and appended `## Question Type\n{qtype}` to the user prompt if present.

### Exact Reason for Each Modification
To allow the benchmark harness to pass a predefined `qtype` (e.g., `"aggregation"`) to the Agentic planner and free-tool calling loop (react) without altering the user's natural language question string or affecting classic vector retrieval behavior. 

### Execution Paths
- **Old execution path**: 
  `NaturalLanguageQuery` -> `retrieve_answer()` -> `AgenticAgent.question_for_agent(question, conversation)` -> `run_agentic(ctx, llm, question, convo)` -> `plan_question(llm, question, conversation, ctx=ctx)`
- **New execution path**: 
  `NaturalLanguageQuery(qtype=...)` -> `retrieve_answer()` -> `AgenticAgent.question_for_agent(question, conversation, qtype=query.qtype)` -> `run_agentic(ctx, llm, question, convo, qtype=qtype)` -> `plan_question(llm, question, conversation, ctx=ctx, qtype=qtype)`

### Runtime Verification Results
A Python test script (`scratch/test_qtype.py`) mocking the LLM API call confirmed that:
- **A.** An existing request WITHOUT `qtype` still executes seamlessly without errors.
- **B.** An Agentic request WITH `qtype` is accepted across the schema and routing path.
- **C.** The planner receives the `qtype` as a separate markdown block (`## Question Type`).
- **D.** The original question string (`## Question`) remains entirely untouched.

### Remaining Limitations
- This `qtype` is currently only exposed to the LLM agent via the system/user prompt during planning or react loops. Deterministic qtype routing has deliberately been avoided per the instructions.
- Classic retrieval methods remain fully agnostic of `qtype`.
## Phase 0C: Execution and Validation

### 1. Verify Repository's Actual Startup/Setup Method
- **Method**: The repository relies primarily on Docker Compose (`docker-compose.yml`) for starting the GraphRAG service, Chat History service, ECC service, UI, and Nginx. 
- **Alternative**: Scripts like `setup_graphrag.sh` are provided for one-step deployment.

### 2. Exact .env Variable Names
- The system configuration primarily uses a JSON file (`configs/server_config.json`) rather than a standard `.env` file for LLM keys (e.g. `OPENAI_API_KEY` mapped inside the JSON).
- The quick start scripts read `LLM_API_KEY` as an environment variable.
- For testing and integration, the following environment variables are recognized: `OPENAI_API_KEY`, `GRAPHRAG_URL`, `DB_CONFIG`, `TG_USERNAME`, `TG_PASSWORD`, `TG_HOST`, `TG_GS_PORT`, `TG_RESTPP_PORT`, `SERVER_CONFIG`.

### 3-8. Application Configuration and Runtime Verification
- **Gate 3 (Configure/Run)**: **SUCCESS** - Docker Desktop (WSL2 backend) is running on Windows. `docker-compose up -d` started successfully. TigerGraph Savanna is connected correctly using secret-based authentication. LLM and embedding providers are configured via `configs/local_server_config.json` (Groq `openai/gpt-oss-120b` for LLM, Gemini `gemini-embedding-001` with dimensionality 1536 for embeddings).
- **Gate 4 (Verify /query)**: **SUCCESS** - Executed classic and aggregation query requests on `/Olympics/query` which resulted in 200 OK responses with successful TigerGraph graph extraction and LLM response generation.
- **Gate 5 (Verify qtype API)**: **SUCCESS** - Passed `qtype="classic"` and `qtype="aggregation"` in actual POST payload to `/Olympics/query`. The system processed it and utilized `map_question_to_schema` and `generate_function` properly.
- **Gate 6 (Ingest 5-doc subset)**: **SUCCESS** - Successfully ingested a 5-document subset (`corpus_5.jsonl`) via the `/ui/Olympics/create_ingest` and `/ui/Olympics/ingest` pipeline. The graph rebuild and ECC pipeline ran successfully.
- **Gate 7 (Similarity search query)**: **SUCCESS** - Executed queries (`Who won gold in canoe sprint?`, `How many athletes won gold medals?`) against the 5 ingested documents. The vector search returned valid documents and the agent successfully returned the expected answer.
- **Gate 8 (Trace fields)**: **SUCCESS** - Confirmed that the real execution produces valid JSON responses containing `natural_language_response`, `answered_question`, and `response_type`.

## Phase 1: Deterministic Infobox Parser & Corpus Forensics

### 1. Exact Corpus Statistics
- **Total Input Documents Analyzed**: 2,951 (processed 100% of `data/corpus.jsonl`).
- **Olympic Event Documents**: 2,162 (73.26% of total corpus).
- **Non-Olympic Distractor Documents**: 789 (26.74% of total corpus).
- **Duplicate Document IDs**: 0 (all 2,951 doc_ids are unique).
- **Duplicate Event Titles**: 0 (all 2,951 titles are unique).

### 2. Infobox Type Distribution
- `Olympic event`: 2,162
- `film`: 549
- `officeholder`: 73
- `person`: 67
- `tennis tournament event`: 25
- `company`: 16
- `NO_INFOBOX` (documents without structured infobox): 11
- `writer`: 9
- `international football competition`: 8
- `scientist`: 6
- `International Handball Competition`: 3
- `aircraft occurrence`: 2
- `military conflict`: 2
- `airline`: 2
- `website`: 2
- `international ice hockey competition`: 2
- `field hockey`: 2
- `Olympic water polo tournament`: 2
- `civilian attack`: 1
- `television`: 1
- `venue`: 1
- `Olympic games`: 1
- Other minor types (1 each): `Song Contest`, `media franchise`, `rugby tournament`, `manner of address`, etc.

### 3. Olympic Field Coverage Statistics (out of 2,162 Olympic documents)
- `event`: 2,162 present (100.00%) | 0 missing
- `games`: 2,162 present (100.00%) | 0 missing
- `gold`: 2,162 present (100.00%) | 0 missing
- `goldNOC`: 2,154 present (99.63%) | 8 missing
- `silver`: 2,155 present (99.68%) | 7 missing
- `silverNOC`: 2,147 present (99.31%) | 15 missing
- `bronze`: 2,155 present (99.68%) | 7 missing
- `bronzeNOC`: 2,145 present (99.21%) | 17 missing
- `date_raw` (date / dates): 2,139 present (98.94%) | 23 missing
- `competitors`: 2,130 present (98.52%) | 32 missing
- `nations`: 2,128 present (98.43%) | 34 missing
- `next`: 2,111 present (97.64%) | 51 missing
- `venue` (venue / venues): 2,100 present (97.13%) | 62 missing
- `prev`: 2,020 present (93.43%) | 142 missing
- `win_value`: 1,384 present (64.01%) | 778 missing

### 4. Parser Implementation Summary
- **Module**: `analysis/infobox_parser.py`
- **Methodology**: Pure Python string and regular expression parsing. Zero LLM calls used.
- **Field Extraction Rules**:
  - `competitors`, `nations`, `prev`, `next`: parsed as `integer` when numeric, `None` if missing/unparseable.
  - `gold`, `silver`, `bronze`: stored as **RAW STRINGS** exactly as they appear in the corpus. Concatenated team names (e.g., `Erik LesserDaniel BöhmArnd PeifferSimon Schempp`) are preserved without adding spaces, commas, or punctuation.
  - `sport`: deterministically recovered from document title via title pattern regex (100% recovery for Olympic titles).
  - Non-Olympic distractor records: retained in analysis and categorized with `is_olympic_event: False`.

### 5. Known Data Irregularities & Parse Failures
- **Parse Failures**: 0 documents failed infobox parsing when `[Infobox Olympic event]` was present.
- **Malformed Numerics**: 0 unparseable numeric values encountered when integer fields were present.
- **Key Variants**: `venues` used in 19 docs (handled via fallback to `venue`); `dates` used in 888 docs (handled via fallback to `date_raw`).
- **Concatenated Team Names**: Team event gold/silver/bronze fields contain multiple athlete names joined together without spaces (e.g., `Rudolf DombiRoland Kókény`). Preserved byte-for-byte in parser output per task constraints.

### 6. Generated Output Files
- **`analysis/infobox_parser.py`**: Pure Python infobox parsing module.
- **`analysis/corpus_forensics.py`**: Corpus-wide forensics execution script.
- **`analysis/verify_parser.py`**: Verification script testing 10 normal, 5 irregular, 5 team concatenated, 5 distractor docs, and raw string assertions.
- **`data/processed/events.jsonl`**: 2,162 structured JSONL records for all Olympic event documents.
- **`analysis/reports/corpus_forensics.json`**: Complete, exact forensic statistics JSON report.

### 7. Validation Results
All verification suites in `analysis/verify_parser.py` passed with 100% compliance:
- 10 Normal Olympic documents parsed correctly.
- 5 Irregular Olympic documents (missing prev/next/venue/competitors) parsed without errors or fake data insertion.
- 5 Team-event documents verified raw string preservation for concatenated medalists.
- 5 Non-Olympic documents correctly identified and classified.
- String preservation test for `Erik LesserDaniel BöhmArnd PeifferSimon Schempp` passed exact equality check.

## Phase 2: Benchmark Harness Architecture & Validation

### 1. Response Contract & Verified API Fields
Direct inspection of `POST /{graphname}/query` confirmed the following response structure:
- **`natural_language_response`**: Main text output returned by LLM (e.g. `"According to the provided corpus..."`).
- **`answered_question`**: Boolean flag indicating if the model successfully processed the query.
- **`response_type`**: Backend router type (e.g. `"supportai"`).
- **`query_sources.token_usage`**: Aggregated token counts (`input_tokens`, `output_tokens`, `total_tokens`, `cost`).
- **`query_sources.citations`**: Verified citations linking answer entities to retrieved graph/document nodes.
- **`query_sources.agent_steps`**: Sequential trace array containing step names (`node`), duration (`duration_s`), step inputs, step outputs, and step token usage.
- **`query_sources.agent_steps[*].output.context.result.final_retrieval`**: Discovered payload exposing retrieved chunk IDs (e.g. `q743905_chunk_1`, `q607635_chunk_2`).

### 2. Public Evaluation Dataset Schema (`data/eval_public.jsonl`)
- **Total Questions**: 100 (100% unique QIDs, 0 duplicate QIDs, 0 missing gold answers).
- **Schema Fields**:
  - `qid` (str): e.g. `"pub-001"`
  - `question` (str): exact question string
  - `qtype` (str): category classifier
  - `answer` (list[str]): gold answer list containing exactly 1 target string
  - `gold_doc_ids` (list[str]): list of relevant document QIDs (e.g. `["Q47091419", ...]`)
  - `answer_named_in_question` (bool), `guess_baseline` (float), `answer_verified` (bool)
- **QType Distribution**:
  - `multi_hop`: 28 (28.0%)
  - `temporal`: 22 (22.0%)
  - `aggregation`: 21 (21.0%)
  - `lookup`: 19 (19.0%)
  - `superlative`: 10 (10.0%)

### 3. Benchmark Harness Design (`benchmark/runner.py`)
- **Execution Mode**: Sends HTTP POST requests to `http://localhost:8000/Olympics/query` using HTTP Basic Authentication (`username` & `password` from `configs/local_server_config.json`).
- **Configurability**:
  - Supports `--all`, `--qid <QID>`, `--qtype <QTYPE>`, and `--limit <N>`.
  - Supports pipeline selection (`--mode classic|agentic`, `--rag-method similaritysearch|hybridsearch`, `--pass-qtype`).
  - Preserves natural language question string untouched; passes `qtype` as payload field only when explicitly requested.
- **Evaluator Rule Disclosure**: No official evaluator was found in the repository; `strict_exact_match` is the reproducible internal benchmark metric.
- **Scoring Rules**:
  - **`strict_exact_match` (Primary Internal Metric)**: Compares `prediction.strip() == gold.strip()`. Deterministic and reproducible.
  - **`normalized_match` (Diagnostic Metric Only)**: Removes Markdown emphasis markers (`**`, `*`, `__`), lowercases strings, and checks if canonical gold answer string occurs within normalized prediction. Serves strictly as a diagnostic signal for answer presence without altering primary benchmark accuracy.
- **Intrusion Metric (`retrieval_intrusion_at_k`)**:
  - Extracts chunk IDs from `agent_steps` (e.g. `q743905_chunk_1`).
  - Maps chunk prefix (`q743905`) to uppercase Wikidata QID (`Q743905`).
  - Measures percentage of retrieved documents that do NOT belong to the 2,162 Olympic-event documents in `data/processed/events.jsonl`.
  - **Limitation**: When 0 chunks are retrieved or chunk IDs are not populated in agent step outputs, intrusion reports `None`/0.0 rather than inventing fallback values.

### 4. Smoke-Test Execution Results (5 Public Questions)
- **Execution Command**: `python benchmark/runner.py --limit 5 --run-name smoke_test`
- **Attempted / Processed**: 5 / 5 questions (100% completion rate without unhandled runner crashes).
- **HTTP Success Rate**: 80.00% (4/5 succeeded within 120s timeout; 1 request timed out cleanly captured in `error` field).
- **Primary Metric (`strict_exact_match`)**: 0 / 5 (0.0% accuracy expected, as only 5 documents were ingested in TigerGraph prior to full corpus ingestion).
- **Diagnostic Metric (`normalized_match`)**: 0 / 5 (0.0%).
- **Average Latency**: 52.043s
- **Output Files Generated**:
  - `benchmark/results/smoke_test.jsonl`: 5 detailed per-question result records with complete traces, latencies, token usages, predictions, `strict_exact_match`, and `normalized_match`.
  - `benchmark/results/smoke_test_summary.json`: Summary statistics report.

### 5. Gate Validation Matrix
1. `benchmark/runner.py` exists and runs: **PASS**
2. Exactly 5 public questions processed in smoke test: **PASS**
3. Result file with 5 records exists (`benchmark/results/smoke_test.jsonl`): **PASS**
4. Exact-match scoring (`strict_exact_match`) is deterministic: **PASS**
5. Diagnostic score (`normalized_match`) recorded separately: **PASS**
6. Raw trace/evidence preserved: **PASS**
7. Errors do not terminate whole run: **PASS**
8. Public evaluation integrity checks pass: **PASS**



