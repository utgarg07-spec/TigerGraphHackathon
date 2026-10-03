# 25Q CONFIDENCE RUN REPORT
**Timestamp:** 2026-10-01T20:52:27.942405
**Total Run Time:** 659.98s

## 1. Executive Summary
- **HTTP Success Rate:** 25/25 (100.0%)
- **Normalized Accuracy:** 22/25 (88.0%)
- **Strict Exact Match:** 1/25 (4.0%)
- **Gold Evidence Hit:** 22/25 (88.0%)
- **Mean Latency:** 26.4s (Median: 16.29s, P95: 76.69s)

## 2. Per-QType Breakdown
| QType | Count | Normalized Accuracy | Strict EM | Gold Evidence Hit | Mean Latency (s) |
|---|---|---|---|---|---|
| lookup | 5 | 100.0% | 0.0% | 100.0% | 28.16s |
| temporal | 5 | 100.0% | 20.0% | 100.0% | 12.97s |
| aggregation | 5 | 100.0% | 0.0% | 100.0% | 15.17s |
| superlative | 5 | 100.0% | 0.0% | 100.0% | 13.57s |
| multi_hop | 5 | 40.0% | 0.0% | 40.0% | 62.12s |

## 3. Question-Level Trace
| QID | QType | HTTP | Latency (s) | Correct | Tools Used | Prediction Excerpt |
|---|---|---|---|---|---|---|
| pub-032 | lookup | SUCCESS | 76.686 | True | graphrag__lookup | 34 nations competed in Gymnastics at the |
| pub-034 | lookup | SUCCESS | 21.772 | True | graphrag__lookup | 23 nations competed in Figure skating at |
| pub-035 | lookup | SUCCESS | 17.18 | True | graphrag__lookup | A total of 30 nations competed in the Me |
| pub-042 | lookup | SUCCESS | 16.293 | True | graphrag__lookup | 47 nations competed in Alpine skiing at  |
| pub-046 | lookup | SUCCESS | 8.876 | True | graphrag__lookup | The Men's 15 kilometre freestyle cross‑c |
| pub-013 | temporal | SUCCESS | 14.104 | True | graphrag__temporal_resolve | Allison Schmitt won the gold medal in th |
| pub-016 | temporal | SUCCESS | 10.763 | True | graphrag__temporal_resolve | Arnd Peiffer won the gold medal in the m |
| pub-018 | temporal | SUCCESS | 13.148 | True | graphrag__temporal_resolve | Kevin Jackson |
| pub-026 | temporal | SUCCESS | 16.112 | True | graphrag__temporal_resolve | Jaroslav Kulhavý won the gold medal in t |
| pub-036 | temporal | SUCCESS | 10.728 | True | graphrag__temporal_resolve | Zou Shiming won the gold medal in the me |
| pub-012 | aggregation | SUCCESS | 15.082 | True | graphrag__aggregate | According to the provided corpus, six ro |
| pub-019 | aggregation | SUCCESS | 18.926 | True | graphrag__aggregate | According to the provided corpus, three  |
| pub-020 | aggregation | SUCCESS | 11.319 | True | graphrag__aggregate | According to the provided corpus, four a |
| pub-024 | aggregation | SUCCESS | 16.999 | True | graphrag__aggregate | According to the provided corpus, three  |
| pub-027 | aggregation | SUCCESS | 13.525 | True | graphrag__aggregate | According to the provided corpus, four f |
| pub-037 | superlative | SUCCESS | 11.982 | True | graphrag__superlative | The shooting event with the highest numb |
| pub-044 | superlative | SUCCESS | 12.948 | True | graphrag__superlative | According to the available structured da |
| pub-053 | superlative | SUCCESS | 17.612 | True | graphrag__superlative | **Shooting at the 2016 Summer Olympics – |
| pub-066 | superlative | SUCCESS | 6.512 | True | graphrag__superlative | According to the available data, the wei |
| pub-084 | superlative | SUCCESS | 18.779 | True | graphrag__superlative | The fencing event with the highest numbe |
| pub-015 | multi_hop | SUCCESS | 119.496 | False | graphrag__hybrid_search,graphrag__structural_retrieve | I wasn't able to generate an answer for  |
| pub-017 | multi_hop | SUCCESS | 69.364 | False | graphrag__hybrid_search | There was no Olympic shooting event held |
| pub-022 | multi_hop | SUCCESS | 25.204 | True | graphrag__hybrid_search | The gold medal was won by **Ayumi Tanimo |
| pub-023 | multi_hop | SUCCESS | 29.208 | True | graphrag__hybrid_search | The gold medal in the men's marathon, wh |
| pub-028 | multi_hop | SUCCESS | 67.32 | False | graphrag__structural_retrieve,graphrag__structural_retrieve | Information unavailable. |

## 4. Failures Encountered
| QID | QType | Question | Prediction | Gold |
|---|---|---|---|---|
| pub-015 | multi_hop | Who won the gold medal in the event held at London Velopark on 3 to 4 August at the 2012 Summer Olympics? | I wasn't able to generate an answer for this question. Try asking again, or rephrase it to be more specific or focused on a single topic. If the problem continues, contact your administrator for more details. | ['Dani KingLaura TrottJoanna Rowsell'] |
| pub-017 | multi_hop | Who won the gold medal in the event held at Royal Artillery Barracks on 28 July 2012? | There was no Olympic shooting event held | ['Yi Siling'] |
| pub-028 | multi_hop | Who won the gold medal in the event held at Olympic Aquatic Centre on August 14, 2004 (heats & final)? | Information unavailable. | ['Michael Phelps'] |
