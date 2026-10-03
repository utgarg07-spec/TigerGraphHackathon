# Phase 7 — Targeted Multi-hop Validation Report

## Executive Summary

- **Target QIDs Tested**: 4 (`pub-005`, `pub-011`, `pub-014`, `pub-015`)
- **Pacing**: Sequential execution with $\ge 25$s between question starts.
- **Provider Infrastructure**:
  - Primary (Groq `openai/gpt-oss-20b`) handled 100% of LLM calls across triage, planning, schema mapping, Cypher generation, and answer synthesis.
  - Periodic transient HTTP 429 rate-limit headers triggered automated client backoff retries (15s–37s), all of which resolved cleanly with HTTP 200.
  - Zero hard provider failures.
- **Core Diagnosis**: **Pure Retrieval / Vector Search Ranking Failure (0% Gold Doc Recall in Top-K)**.
  - **Planner Decomposition**: **Healthy** — Planner correctly identified multi-hop intent and planned structural retrieval followed by hybrid search fallback.
  - **Structural Graph Retrieval**: Cypher queries attempted exact property matching on `venue_name` and `date_raw`. Because event dates in the graph/corpus use diverse raw strings or unstructured infobox formats, Cypher exact matches returned 0 records.
  - **Hybrid / Vector Search**: Fallback to Qwen embedding vector search executed properly, but the dense vector retriever failed to rank the Gold document into the top-5 chunks for all 4 queries.
  - **Synthesis**: **Faithful to Evidence** — Given that the gold documents were absent from the retrieved top-K context, the LLM either hallucinated based on the nearest distractor chunk (`pub-005`) or faithfully reported that no event was found on that date (`pub-011`, `pub-014`, `pub-015`).

---

## Comparative Results Table

| QID | Planned Path | Actual Path | Provider | Fallback | Gold Doc Retrieved | Final Answer Correct | Failure Layer |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **pub-005** | `graphrag__structural_retrieve` → `answer` | `plan` → `structural_retrieve` → `hybrid_search` → `answer` | Groq | No | **No** (0/1) | **No** | **Retrieval (Dense Vector Ranking)** |
| **pub-011** | `graphrag__structural_retrieve` → `answer` | `plan` → `structural_retrieve` → `hybrid_search` → `answer` | Groq | No | **No** (0/1) | **No** | **Retrieval (Dense Vector Ranking)** |
| **pub-014** | `graphrag__hybrid_search` → `answer` | `plan` → `hybrid_search` → `answer` | Groq | No | **No** (0/1) | **No** | **Retrieval (Dense Vector Ranking)** |
| **pub-015** | `graphrag__structural_retrieve` → `answer` | `plan` → `structural_retrieve` → `hybrid_search` → `answer` | Groq | No | **No** (0/1) | **No** | **Retrieval (Dense Vector Ranking)** |

---

## Detailed Execution Traces

### 1. `pub-005`
- **Question**: "Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?"
- **Gold Answer**: `["Naim Süleymanoğlu"]`
- **Gold Doc IDs**: `["Q25239316"]` (Weightlifting at the 1988 Summer Olympics – Men's 60 kg)
- **Generated Answer**: *"The gold medal in the event held at the Olympic Weightlifting Gymnasium on 20 September 1988 was won by **Joachim Kunz** of the German Democratic Republic (GDR)."*
- **Normalized Evaluator Result**: `False`
- **Manual Factual Correctness**: `False` (Joachim Kunz won Men's 67.5 kg on 21 September 1988, not 20 September 1988)

#### Multi-Hop Execution Trace:
```
Question ("Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?")
  │
  ▼
Triage (Classification: Multi-hop retrieval)
  │
  ▼
Plan (Step 1: graphrag__structural_retrieve, Step 2: answer)
  │
  ▼
Tool Step 1: graphrag__structural_retrieve
  ├── Map Question to Schema -> Vertex Event, NOCCountry
  ├── Generate Cypher:
  │     MATCH (v_venue:Venue)-[:HOSTED_EVENT]->(e_event:Event)
  │     WHERE toLower(v_venue.name) CONTAINS "olympic weightlifting gymnasium"
  │       AND toLower(e_event.date_raw) CONTAINS "20 september 1988"
  │     MATCH (e_event)-[:WON_BY_GOLD]-(n_country:NOCCountry)
  │     RETURN e_event, n_country;
  └── Result: Empty (0 rows returned)
  │
  ▼
Tool Step 2 (Fallback): graphrag__hybrid_search
  ├── Query: "Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?"
  ├── Embed Query via Ollama (Qwen)
  ├── TigerGraph Vector Search (Top-5 chunks):
  │     1. Q508776_chunk_0 (Men's 67.5 kg, Joachim Kunz, 21 September 1988)
  │     2. Q269521_chunk_0 (Women's 48 kg, 2008)
  │     3. Q25239321_chunk_0 (Men's 82.5 kg)
  │     4. Q25239533_chunk_0 (Men's 100 kg)
  │     5. Q25239314_chunk_0 (Men's 52 kg, 18 September 1988)
  └── Gold Doc Q25239316 NOT in top-5!
  │
  ▼
Evidence (5 distractor chunks; chunk 1 mentions Joachim Kunz at Olympic Weightlifting Gymnasium)
  │
  ▼
Synthesis (generate_answer)
  └── Uses chunk 1 evidence and concludes Joachim Kunz won on 20 September 1988.
  │
  ▼
Answer ("...won by Joachim Kunz...")
```

- **LLM Calls**: 6 | **Plan Retries**: 1 | **Agent Steps**: 2 | **Latency**: 44.74s
- **Provider**: Groq (`openai/gpt-oss-20b`) | **Fallback Transitions**: None

---

### 2. `pub-011`
- **Question**: "Who won the gold medal in the event held at Richmond Olympic Oval on 14 February 2010?"
- **Gold Answer**: `["Martina Sáblíková"]`
- **Gold Doc IDs**: `["Q580481"]` (Speed skating at the 2010 Winter Olympics – Women's 3000 metres)
- **Generated Answer**: *"There was no Olympic speed‑skating event held at the Richmond Olympic Oval on 14 February 2010, so no gold medal was awarded on that date."*
- **Normalized Evaluator Result**: `False`
- **Manual Factual Correctness**: `False` (Martina Sáblíková won gold on 14 February 2010)

#### Multi-Hop Execution Trace:
```
Question ("Who won the gold medal in the event held at Richmond Olympic Oval on 14 February 2010?")
  │
  ▼
Triage (Classification: Multi-hop retrieval)
  │
  ▼
Plan (Step 1: graphrag__structural_retrieve, Step 2: answer)
  │
  ▼
Tool Step 1: graphrag__structural_retrieve
  ├── Cypher:
  │     MATCH (e:Event)
  │     WHERE toLower(e.venue_name) = "richmond olympic oval"
  │       AND toLower(e.date_raw) = "14 february 2010"
  │     RETURN e.gold AS gold_medalist, e.venue_name AS venue, e.date_raw AS event_date;
  └── Result: Empty (0 rows returned)
  │
  ▼
Tool Step 2 (Fallback): graphrag__hybrid_search
  ├── Embed Query via Ollama (Qwen)
  ├── TigerGraph Vector Search (Top-5 chunks):
  │     1. Q586729_chunk_0 (Speed skating, Men's 5000m, 13 February 2010)
  │     2. Q905540_chunk_0 (Speed skating, Men's 1000m, 17 February 2010)
  │     3. Q848666_chunk_0 (Speed skating, Men's 1500m, 20 February 2010)
  │     4. q595972_chunk_0 (Speed skating, Men's 500m, 15 February 2010)
  │     5. Q848696_chunk_0 (Speed skating, Women's 1000m, 18 February 2010)
  └── Gold Doc Q580481 (Women's 3000m, 14 Feb) NOT in top-5!
  │
  ▼
Evidence (5 Speed Skating chunks from Richmond Oval, but dates are 13, 15, 17, 18, 20 Feb)
  │
  ▼
Synthesis (generate_answer)
  └── LLM checks provided dates in context, finds 14 Feb missing, and concludes no event held on 14 Feb.
  │
  ▼
Answer ("There was no Olympic speed‑skating event held at the Richmond Olympic Oval on 14 February 2010...")
```

- **LLM Calls**: 6 | **Plan Retries**: 0 | **Agent Steps**: 2 | **Latency**: 100.89s
- **Provider**: Groq (`openai/gpt-oss-20b`) | **Fallback Transitions**: None

---

### 3. `pub-014`
- **Question**: "Who won the gold medal in the event held at Riocentro – Pavilion 4 on 11–19 August at the 2016 Summer Olympics?"
- **Gold Answer**: `["Carolina Marín"]`
- **Gold Doc IDs**: `["Q25301483"]` (Badminton at the 2016 Summer Olympics – Women's singles)
- **Generated Answer**: *"Information unavailable."*
- **Normalized Evaluator Result**: `False`
- **Manual Factual Correctness**: `False`

#### Multi-Hop Execution Trace:
```
Question ("Who won the gold medal in the event held at Riocentro – Pavilion 4 on 11–19 August at the 2016 Summer Olympics?")
  │
  ▼
Triage (Classification: Multi-hop retrieval)
  │
  ▼
Plan (Step 1: graphrag__hybrid_search, Step 2: answer)
  │
  ▼
Tool Step 1: graphrag__hybrid_search
  ├── Embed Query via Ollama (Qwen)
  ├── TigerGraph Vector Search (Top-5 chunks):
  │     1. Q26256651_chunk_0 (Table tennis at Riocentro - Pavilion 3)
  │     2. Q25476761_chunk_0 (Boxing at Riocentro - Pavilion 6)
  │     3. Q22968979_chunk_0 (Table tennis at Riocentro - Pavilion 3)
  │     4. Q26217860_chunk_0 (Table tennis at Riocentro - Pavilion 3)
  │     5. Q26254891_chunk_0 (Sailing at Marina da Glória)
  └── Gold Doc Q25301483 (Badminton at Pavilion 4) NOT in top-5!
  │
  ▼
Evidence (Chunks for Pavilions 3, 6, Marina da Glória; none for Pavilion 4)
  │
  ▼
Synthesis (generate_answer)
  └── Notes no evidence matches Pavilion 4 on 11–19 August.
  │
  ▼
Answer ("Information unavailable.")
```

- **LLM Calls**: 3 | **Plan Retries**: 1 | **Agent Steps**: 1 | **Latency**: 73.78s
- **Provider**: Groq (`openai/gpt-oss-20b`) | **Fallback Transitions**: None

---

### 4. `pub-015`
- **Question**: "Who won the gold medal in the event held at London Velopark on 3 to 4 August at the 2012 Summer Olympics?"
- **Gold Answer**: `["Dani KingLaura TrottJoanna Rowsell"]`
- **Gold Doc IDs**: `["Q2297633"]` (Cycling at the 2012 Summer Olympics – Women's team pursuit)
- **Generated Answer**: *"No Olympic cycling event was held at the London Velopark on 3 to 4 August 2012, so there was no gold‑medal winner for that date."*
- **Normalized Evaluator Result**: `False`
- **Manual Factual Correctness**: `False` (Dani King, Laura Trott, Joanna Rowsell won gold on 3–4 August 2012)

#### Multi-Hop Execution Trace:
```
Question ("Who won the gold medal in the event held at London Velopark on 3 to 4 August at the 2012 Summer Olympics?")
  │
  ▼
Triage (Classification: Multi-hop retrieval)
  │
  ▼
Plan (Step 1: graphrag__structural_retrieve, Step 2: answer)
  │
  ▼
Tool Step 1: graphrag__structural_retrieve
  ├── Cypher:
  │     MATCH (e:Event)
  │     WHERE toLower(e.venue_name) CONTAINS "london velopark" 
  │       AND toLower(e.date_raw) CONTAINS "3 to 4 august"
  │     RETURN e, e.gold;
  └── Result: Empty (0 rows returned)
  │
  ▼
Tool Step 2 (Fallback): graphrag__hybrid_search
  ├── Embed Query via Ollama (Qwen)
  ├── TigerGraph Vector Search (Top-5 chunks):
  │     1. Q2718019_chunk_0 (Cycling, Men's BMX, 8–10 August)
  │     2. Q2269694_chunk_0 (Cycling, Men's sprint, 4–6 August)
  │     3. Q1005298_chunk_0 (Cycling, Men's keirin, 7 August)
  │     4. Q2362858_chunk_0 (Cycling, Men's team sprint, 2 August)
  │     5. Q2194130_chunk_0 (Cycling, Men's omnium, 4–5 August)
  └── Gold Doc Q2297633 (Women's team pursuit, 3–4 August) NOT in top-5!
  │
  ▼
Evidence (5 Cycling chunks from London Velopark, but none for Women's team pursuit 3–4 August)
  │
  ▼
Synthesis (generate_answer)
  └── Evaluates retrieved event dates, finds no event covering 3 to 4 August.
  │
  ▼
Answer ("No Olympic cycling event was held at the London Velopark on 3 to 4 August 2012...")
```

- **LLM Calls**: 6 | **Plan Retries**: 1 | **Agent Steps**: 2 | **Latency**: 112.13s
- **Provider**: Groq (`openai/gpt-oss-20b`) | **Fallback Transitions**: None
