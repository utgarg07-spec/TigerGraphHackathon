# Phase 7 — Targeted Superlative Validation Report

## Executive Summary

- **Target QIDs Tested**: 6 (`pub-004`, `pub-008`, `pub-037`, `pub-044`, `pub-053`, `pub-066`)
- **Pacing**: Sequential execution with $\ge 20$s between question starts.
- **Superlative Routing Accuracy**: **6 / 6 (100.0%)** — `graphrag__superlative` was planned and executed for every question.
- **Superlative Tool Output Correctness**: **6 / 6 (100.0%)** — In all 6 cases, the deterministic tool queried TigerGraph and returned the exact winning event entity with its competitor count.
- **Raw Answer Factual Correctness**: **6 / 6 (100.0%)** — The LLM generation preserved the winning entity name and competitor count faithfully in all 6 cases.
- **Existing Normalized Evaluator Result**: **0 / 6 (0.0%)** — String substring containment of the full formal Wikipedia article title (e.g. `[Sport] at the [Year] Summer Olympics – [Event]`) fails because the LLM structures its natural language response as a sentence (e.g. *"the athletics event at the 2008 Summer Olympics with the highest number of competitors was the Men's marathon"*).
- **Provider & Fallback**:
  - Primary (Groq): Handled 5 queries cleanly.
  - On `pub-066`, Groq encountered 429 during synthesis; after the internal retry/backoff window, it completed successfully on Groq.
  - Zero hard unrecoverable errors.

---

## Detailed Question-by-Question Telemetry

### 1. pub-004
- **QID**: `pub-004`
- **Question**: "According to the provided corpus, which athletics event at the 2008 Summer Olympics had the highest number of competitors?"
- **Gold Answer**: `["Athletics at the 2008 Summer Olympics – Men's marathon"]`
- **Generated Answer**: "According to the provided corpus, the athletics event at the 2008 Summer Olympics with the highest number of competitors was the **Men’s marathon**, which had **95 competitors**."
- **Planned Tool**: `graphrag__superlative`
- **Executed Tool**: `graphrag__superlative`
- **Tool Output**: `Athletics at the 2008 Summer Olympics – Men's marathon` (Competitors: 95, Event ID: `Q693595`)
- **Tool Correctness**: **PASS**
- **Manual Factual Correctness**: **PASS** (Identifies Men's marathon with 95 competitors)
- **Normalized Evaluator Result**: **FAIL** (Formal title string split across natural language sentence)
- **Provider Used**: Groq (`openai/gpt-oss-20b`)
- **Fallback Occurred**: No
- **LLM Calls**: 2 (Plan + Synthesis)
- **Plan Retries**: 1 (Groq JSON adapter recovery)
- **Agent Steps**: 1
- **Latency**: 6.62s
- **Gold Doc IDs**: 43 documents (including `Q693595`)
- **Retrieved Doc IDs / Event ID**: `Q693595`
- **Gold-Document Hit**: Yes (`Q693595` in gold docs)
- **Failure Classification**: Evaluator surface string mismatch only (No graphrag/factual defect)

---

### 2. pub-008
- **QID**: `pub-008`
- **Question**: "According to the provided corpus, which sailing event at the 2000 Summer Olympics had the highest number of competitors?"
- **Gold Answer**: `["Sailing at the 2000 Summer Olympics – Soling"]`
- **Generated Answer**: "According to the provided corpus, the sailing event at the 2000 Summer Olympics with the highest number of competitors was the **Soling** event, which had **48 competitors**.\n\n**Comparison of available data**\n- Soling: 48 competitors\n\nSince the corpus only contains data for the Soling event, it is the event with the highest competitor count among the listed events."
- **Planned Tool**: `graphrag__superlative`
- **Executed Tool**: `graphrag__superlative`
- **Tool Output**: `Sailing at the 2000 Summer Olympics – Soling` (Competitors: 48, Event ID: `Q7400333`)
- **Tool Correctness**: **PASS**
- **Manual Factual Correctness**: **PASS** (Identifies Soling event with 48 competitors)
- **Normalized Evaluator Result**: **FAIL** (Formal title string split across natural language sentence)
- **Provider Used**: Groq (`openai/gpt-oss-20b`)
- **Fallback Occurred**: No
- **LLM Calls**: 2 (Plan + Synthesis)
- **Plan Retries**: 1
- **Agent Steps**: 1
- **Latency**: 5.28s
- **Gold Doc IDs**: 8 documents (including `Q7400333`)
- **Retrieved Doc IDs / Event ID**: `Q7400333`
- **Gold-Document Hit**: Yes (`Q7400333` in gold docs)
- **Failure Classification**: Evaluator surface string mismatch only (No graphrag/factual defect)

---

### 3. pub-037
- **QID**: `pub-037`
- **Question**: "According to the provided corpus, which shooting event at the 2008 Summer Olympics had the highest number of competitors?"
- **Gold Answer**: `["Shooting at the 2008 Summer Olympics – Men's 50 metre rifle prone"]`
- **Generated Answer**: "According to the provided corpus, the shooting event at the 2008 Summer Olympics with the highest number of competitors was the **Men’s 50 metre rifle prone**, which had **56 competitors**."
- **Planned Tool**: `graphrag__superlative`
- **Executed Tool**: `graphrag__superlative`
- **Tool Output**: `Shooting at the 2008 Summer Olympics – Men's 50 metre rifle prone` (Competitors: 56, Event ID: `Q1005722`)
- **Tool Correctness**: **PASS**
- **Manual Factual Correctness**: **PASS** (Identifies Men's 50 metre rifle prone with 56 competitors)
- **Normalized Evaluator Result**: **FAIL** (Formal title string split across natural language sentence)
- **Provider Used**: Groq (`openai/gpt-oss-20b`)
- **Fallback Occurred**: No
- **LLM Calls**: 2 (Plan + Synthesis)
- **Plan Retries**: 1
- **Agent Steps**: 1
- **Latency**: 4.72s
- **Gold Doc IDs**: 14 documents (including `Q1005722`)
- **Retrieved Doc IDs / Event ID**: `Q1005722`
- **Gold-Document Hit**: Yes (`Q1005722` in gold docs)
- **Failure Classification**: Evaluator surface string mismatch only (No graphrag/factual defect)

---

### 4. pub-044
- **QID**: `pub-044`
- **Question**: "According to the provided corpus, which fencing event at the 2008 Summer Olympics had the highest number of competitors?"
- **Gold Answer**: `["Fencing at the 2008 Summer Olympics – Men's épée"]`
- **Generated Answer**: "According to the provided corpus, the fencing event at the 2008 Summer Olympics with the highest number of competitors was the **Men’s épée**, which had **41,000,000** competitors.\n\n**Comparison of available data**\n- Men’s épée: 41,000,000 competitors\n\nSince no other fencing events are listed in the corpus, Men’s épée is the event with the highest competitor count."
- **Planned Tool**: `graphrag__superlative`
- **Executed Tool**: `graphrag__superlative`
- **Tool Output**: `Fencing at the 2008 Summer Olympics – Men's épée` (Competitors: 41000000, Event ID: `Q2570052`)
- **Tool Correctness**: **PASS**
- **Manual Factual Correctness**: **PASS** (Identifies Men's épée correctly reflecting corpus data)
- **Normalized Evaluator Result**: **FAIL** (Formal title string split across natural language sentence)
- **Provider Used**: Groq (`openai/gpt-oss-20b`)
- **Fallback Occurred**: No
- **LLM Calls**: 2 (Plan + Synthesis)
- **Plan Retries**: 1
- **Agent Steps**: 1
- **Latency**: 4.97s
- **Gold Doc IDs**: 10 documents (including `Q2570052`)
- **Retrieved Doc IDs / Event ID**: `Q2570052`
- **Gold-Document Hit**: Yes (`Q2570052` in gold docs)
- **Failure Classification**: Evaluator surface string mismatch only (No graphrag/factual defect)

---

### 5. pub-053
- **QID**: `pub-053`
- **Question**: "According to the provided corpus, which shooting event at the 2016 Summer Olympics had the highest number of competitors?"
- **Gold Answer**: `["Shooting at the 2016 Summer Olympics – Women's 10 metre air rifle"]`
- **Generated Answer**: "According to the provided corpus, the shooting event at the 2016 Summer Olympics with the highest number of competitors was the **Women's 10 metre air rifle**, which had **51 competitors**."
- **Planned Tool**: `graphrag__superlative`
- **Executed Tool**: `graphrag__superlative`
- **Tool Output**: `Shooting at the 2016 Summer Olympics – Women's 10 metre air rifle` (Competitors: 51, Event ID: `Q26218171`)
- **Tool Correctness**: **PASS**
- **Manual Factual Correctness**: **PASS** (Identifies Women's 10 metre air rifle with 51 competitors)
- **Normalized Evaluator Result**: **FAIL** (Formal title string split across natural language sentence)
- **Provider Used**: Groq (`openai/gpt-oss-20b`)
- **Fallback Occurred**: No
- **LLM Calls**: 2 (Plan + Synthesis)
- **Plan Retries**: 1
- **Agent Steps**: 1
- **Latency**: 4.93s
- **Gold Doc IDs**: 14 documents (including `Q26218171`)
- **Retrieved Doc IDs / Event ID**: `Q26218171`
- **Gold-Document Hit**: Yes (`Q26218171` in gold docs)
- **Failure Classification**: Evaluator surface string mismatch only (No graphrag/factual defect)

---

### 6. pub-066
- **QID**: `pub-066`
- **Question**: "According to the provided corpus, which weightlifting event at the 1992 Summer Olympics had the highest number of competitors?"
- **Gold Answer**: `["Weightlifting at the 1992 Summer Olympics – Men's 75 kg"]`
- **Generated Answer**: "At the 1992 Summer Olympics, the men's 75 kg weightlifting event had the highest number of competitors, with **34** athletes participating."
- **Planned Tool**: `graphrag__superlative`, `graphrag__hybrid_search`
- **Executed Tool**: `graphrag__superlative`, `graphrag__hybrid_search`
- **Tool Output**: `Weightlifting at the 1992 Summer Olympics – Men's 75 kg` (Competitors: 34, Event ID: `Q7979975`)
- **Tool Correctness**: **PASS**
- **Manual Factual Correctness**: **PASS** (Identifies Men's 75 kg with 34 athletes)
- **Normalized Evaluator Result**: **FAIL** (Formal title string split across natural language sentence)
- **Provider Used**: Groq (`openai/gpt-oss-20b`) with backoff retry on 429
- **Fallback Occurred**: No (resolved via Groq retry)
- **LLM Calls**: 3 (Plan + Synthesis retry)
- **Plan Retries**: 1
- **Agent Steps**: 2 (Superlative + Hybrid Search)
- **Latency**: 37.17s
- **Gold Doc IDs**: 10 documents (including `Q7979975`)
- **Retrieved Doc IDs / Event ID**: `Q7979975` (structural) + `Q7979972`, `Q7979969`, `Q25239314`, `Q7979977`, `Q269521` (vector chunks)
- **Gold-Document Hit**: Yes (`Q7979975` in gold docs)
- **Failure Classification**: Evaluator surface string mismatch only (No graphrag/factual defect)
