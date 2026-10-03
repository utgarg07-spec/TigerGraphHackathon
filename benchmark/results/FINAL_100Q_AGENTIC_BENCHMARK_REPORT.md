# FINAL 100Q AGENTIC BENCHMARK REPORT
**Timestamp:** 2026-10-02T09:59:30.554007
**Total Run Time:** 3943.0s
**Model / Service:** openai/gpt-oss-20b via airouter

## 1. Executive Summary
- **HTTP Success Rate:** 100/100 (100.0%)
- **Normalized Accuracy:** 95/100 (95.0%)
- **Strict Exact Match:** 0/100 (0.0%)
- **Gold Evidence Hit:** 95/100 (95.0%)
- **Mean Latency:** 39.43s (Median: 25.22s, P95: 116.35s, Max: 358.78s)

## 2. Per-QType Breakdown
| QType | Count | Normalized Accuracy | Strict EM | Gold Evidence Hit | Mean Latency (s) |
|---|---|---|---|---|---|
| aggregation | 21 | 100.0% | 0.0% | 100.0% | 26.51s |
| temporal | 22 | 100.0% | 0.0% | 100.0% | 43.52s |
| superlative | 10 | 100.0% | 0.0% | 100.0% | 22.46s |
| multi_hop | 28 | 82.1% | 0.0% | 82.1% | 48.22s |
| lookup | 19 | 100.0% | 0.0% | 100.0% | 44.94s |

## 3. Comparative Evolution vs Baseline
| Paradigm | Accuracy | Strict EM | Evidence Grounding | Mean Latency |
|---|---|---|---|---|
| Vector RAG Baseline | 43.0% | 28.0% | 41.0% | 4.82s |
| GraphRAG Baseline | 64.0% | 51.0% | 61.0% | 7.91s |
| **Final Agentic GraphRAG** | **95/100 (95.0%)** | **0/100 (0.0%)** | **95/100 (95.0%)** | **39.43s** |

## 4. Failure Register
| QID | QType | Question | Prediction | Gold |
|---|---|---|---|---|
| pub-015 | multi_hop | Who won the gold medal in the event held at London Velopark on 3 to 4 August at the 2012 Summer Olympics? | **Men’s cycling omnium – 2012 Summer Olympics (London Velopark, 4–5 August)**  The gold medal was won by **Lasse Norman Hansen** of Denmark.  ---  *Source: Q2437166_chunk_0* | ['Dani KingLaura TrottJoanna Rowsell'] |
| pub-038 | multi_hop | Who won the gold medal in the event held at Sydney Convention and Exhibition Centre on 23 September 2000? | **Men’s super‑heavyweight boxing at the 2000 Summer Olympics** – The gold medal was won by **Audley Harrison** of Great Britain.  The competition began on 23 September 2000 at the Sydney Convention and Exhibition Centre and concluded on 1 October 2000. Harrison secured the top podium spot in the 91 kg+ category.  ---  *Citation:* Q4951847_chunk_0 | ['Pyrros Dimas'] |
| pub-060 | multi_hop | Who won the gold medal in the event held at ExCeL Exhibition Centre on 30 July at the 2012 Summer Olympics? | The following Olympic events took place at the ExCeL Exhibition Centre on 30 July 2012, along with their gold‑medal winners:  - **Women's 57kg competition in judo at the 2012 Summer Olympics in London** – Kaori Matsumoto (JPN) - **Men's 73kg competition in judo at the 2012 Summer Olympics in London** – Mansur Isaev (RUS) - **Women's | ['Yana Shemyakina'] |
| pub-076 | multi_hop | Who won the gold medal in the event held at Sestriere on February 24, 2006? | I wasn't able to generate an answer for this question. Try asking again, or rephrase it to be more specific or focused on a single topic. If the problem continues, contact your administrator for more details. | ['Julia Mancuso'] |
| pub-098 | multi_hop | Who won the gold medal in the event held at Sydney Convention and Exhibition Centre on 18 September to 1 October 2000? | **Men’s heavyweight boxing** – The gold medal was won by **Félix Savón** of Cuba. | ['Bekzat Sattarkhanov'] |
