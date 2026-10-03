"""
Recompute benchmark evidence telemetry and multi-category gold hit metrics offline (Gates 8, 9, 11).
Consumes benchmark/results/agentic_full_100.jsonl and data/eval_public.jsonl.
Preserves original artifacts untouched and writes repaired outputs.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

from benchmark.evidence_evaluator import (
    extract_evidence_from_payload,
    evaluate_gold_evidence,
    normalize_evidence_id,
)
from benchmark.runner import (
    load_olympic_doc_ids,
    load_evaluation_dataset,
    compute_normalized_match,
)


def recompute_benchmark_evidence(
    raw_results_path: str = "benchmark/results/agentic_full_100.jsonl",
    eval_path: str = "data/eval_public.jsonl",
    output_jsonl_path: str = "benchmark/results/agentic_full_100_evidence_recomputed.jsonl",
    output_summary_path: str = "benchmark/results/agentic_full_100_evidence_summary.json",
):
    olympic_doc_ids = load_olympic_doc_ids("data/processed/events.jsonl")
    gold_records = {r["qid"]: r for r in load_evaluation_dataset(eval_path)}

    with open(raw_results_path, "r", encoding="utf-8") as f:
        raw_records = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(raw_records)} raw benchmark records from {raw_results_path}")

    recomputed_records = []
    qtype_stats = {}

    for r in raw_records:
        qid = r["qid"]
        qtype = r["qtype"]
        gold_rec = gold_records.get(qid, {})
        gold_doc_ids = gold_rec.get("gold_doc_ids", r.get("gold_doc_ids", []))
        gold_answers = gold_rec.get("answer", [r.get("gold", "")])
        gold_str = gold_answers[0] if isinstance(gold_answers, list) and len(gold_answers) > 0 else str(gold_answers)
        prediction = r.get("prediction", "")
        error_info = r.get("error")

        # Extract comprehensive evidence
        agent_steps = r.get("agent_steps") or []
        citations = r.get("citations") or []
        
        evidence = extract_evidence_from_payload(
            query_sources={"agent_steps": agent_steps, "citations": citations},
            agent_steps=agent_steps,
            citations=citations,
            olympic_doc_ids=olympic_doc_ids,
        )

        # Multi-category gold hit evaluation
        eval_res = evaluate_gold_evidence(
            evidence=evidence,
            gold_doc_ids=gold_doc_ids,
            qtype=qtype,
            error=error_info,
        )

        # Accuracy checks
        strict_exact_match = (prediction.strip() == gold_str.strip()) if prediction else False
        normalized_match = compute_normalized_match(prediction, gold_str) if prediction else False

        rec_out = {
            "qid": qid,
            "qtype": qtype,
            "question": r.get("question", gold_rec.get("question", "")),
            "prediction": prediction,
            "gold": gold_str,
            "gold_doc_ids": gold_doc_ids,
            "strict_exact_match": strict_exact_match,
            "normalized_match": normalized_match,
            "correct": strict_exact_match or normalized_match,
            # Disaggregated evidence
            "retrieved_chunk_ids": evidence["retrieved_chunk_ids"],
            "retrieved_doc_ids": evidence["retrieved_doc_ids"],
            "retrieved_vertex_ids": evidence["retrieved_vertex_ids"],
            "cited_chunk_ids": evidence["cited_chunk_ids"],
            "cited_doc_ids": evidence["cited_doc_ids"],
            "cited_vertex_ids": evidence["cited_vertex_ids"],
            "deterministic_tools_used": evidence["deterministic_tools_used"],
            "deterministic_tool_evidence": evidence["deterministic_tool_evidence"],
            "retrieval_intrusion_at_k": evidence["retrieval_intrusion_at_k"],
            # Disaggregated gold metrics
            "gold_chunk_hit": eval_res["gold_chunk_hit"],
            "gold_vertex_hit": eval_res["gold_vertex_hit"],
            "gold_tool_evidence_hit": eval_res["gold_tool_evidence_hit"],
            "cited_gold_hit": eval_res["cited_gold_hit"],
            "gold_doc_hit": eval_res["gold_hit_combined"],
            # Latency / Provider metadata
            "latency": r.get("latency"),
            "token_usage": r.get("token_usage"),
            "provider": r.get("provider", "Groq (openai/gpt-oss-20b via FreeLLMAPI)"),
            "citations": citations,
            "agent_steps": agent_steps,
            "plan": r.get("plan"),
            "error": error_info,
        }
        recomputed_records.append(rec_out)

        # Update QType stats
        if qtype not in qtype_stats:
            qtype_stats[qtype] = {
                "count": 0,
                "strict": 0,
                "norm": 0,
                "gold_chunk_hit": 0,
                "gold_chunk_na": 0,
                "gold_vertex_hit": 0,
                "gold_vertex_na": 0,
                "gold_tool_hit": 0,
                "gold_tool_na": 0,
                "cited_hit": 0,
                "gold_combined_hit": 0,
                "intrusion_vals": [],
                "errors": 0,
            }
        st = qtype_stats[qtype]
        st["count"] += 1
        if strict_exact_match:
            st["strict"] += 1
        if normalized_match:
            st["norm"] += 1
        if error_info:
            st["errors"] += 1

        # Chunk hit
        if eval_res["gold_chunk_hit"] is True:
            st["gold_chunk_hit"] += 1
        elif eval_res["gold_chunk_hit"] is None:
            st["gold_chunk_na"] += 1

        # Vertex hit
        if eval_res["gold_vertex_hit"] is True:
            st["gold_vertex_hit"] += 1
        elif eval_res["gold_vertex_hit"] is None:
            st["gold_vertex_na"] += 1

        # Tool hit
        if eval_res["gold_tool_evidence_hit"] is True:
            st["gold_tool_hit"] += 1
        elif eval_res["gold_tool_evidence_hit"] is None:
            st["gold_tool_na"] += 1

        if eval_res["cited_gold_hit"]:
            st["cited_hit"] += 1
        if eval_res["gold_hit_combined"]:
            st["gold_combined_hit"] += 1

        if evidence["retrieval_intrusion_at_k"] is not None:
            st["intrusion_vals"].append(evidence["retrieval_intrusion_at_k"])

    # Write recomputed JSONL
    Path(output_jsonl_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl_path, "w", encoding="utf-8") as f_out:
        for rec in recomputed_records:
            f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Aggregate summary
    total_attempted = len(recomputed_records)
    total_successful = sum(1 for r in recomputed_records if r.get("error") is None)
    total_failed = sum(1 for r in recomputed_records if r.get("error") is not None)
    total_strict = sum(1 for r in recomputed_records if r.get("strict_exact_match"))
    total_norm = sum(1 for r in recomputed_records if r.get("normalized_match"))
    total_combined_hit = sum(1 for r in recomputed_records if r.get("gold_doc_hit"))

    all_intrusions = [r["retrieval_intrusion_at_k"] for r in recomputed_records if r.get("retrieval_intrusion_at_k") is not None]
    avg_intrusion = round(sum(all_intrusions) / len(all_intrusions), 2) if all_intrusions else None

    qtype_summary = {}
    for qt, s in qtype_stats.items():
        cnt = s["count"]
        chunk_evaluable = cnt - s["gold_chunk_na"]
        vertex_evaluable = cnt - s["gold_vertex_na"]
        tool_evaluable = cnt - s["gold_tool_na"]

        qtype_summary[qt] = {
            "attempted": cnt,
            "strict_exact_match_count": s["strict"],
            "strict_exact_match_pct": round((s["strict"] / cnt) * 100, 2),
            "normalized_match_count": s["norm"],
            "normalized_match_pct": round((s["norm"] / cnt) * 100, 2),
            "gold_chunk_hit_count": s["gold_chunk_hit"],
            "gold_chunk_hit_pct": round((s["gold_chunk_hit"] / chunk_evaluable) * 100, 2) if chunk_evaluable > 0 else None,
            "gold_chunk_na_count": s["gold_chunk_na"],
            "gold_vertex_hit_count": s["gold_vertex_hit"],
            "gold_vertex_hit_pct": round((s["gold_vertex_hit"] / vertex_evaluable) * 100, 2) if vertex_evaluable > 0 else None,
            "gold_vertex_na_count": s["gold_vertex_na"],
            "gold_tool_evidence_hit_count": s["gold_tool_hit"],
            "gold_tool_evidence_hit_pct": round((s["gold_tool_hit"] / tool_evaluable) * 100, 2) if tool_evaluable > 0 else None,
            "gold_tool_na_count": s["gold_tool_na"],
            "cited_gold_hit_count": s["cited_hit"],
            "gold_combined_hit_count": s["gold_combined_hit"],
            "gold_combined_hit_pct": round((s["gold_combined_hit"] / cnt) * 100, 2),
            "retrieval_intrusion_computable_count": len(s["intrusion_vals"]),
            "retrieval_intrusion_na_count": cnt - len(s["intrusion_vals"]),
            "average_retrieval_intrusion_pct": round(sum(s["intrusion_vals"]) / len(s["intrusion_vals"]), 2) if s["intrusion_vals"] else None,
            "errors": s["errors"],
        }

    summary_report = {
        "run_name": "agentic_full_100_evidence_recomputed",
        "number_attempted": total_attempted,
        "number_successful": total_successful,
        "number_failed": total_failed,
        "http_success_rate": round(total_successful / total_attempted, 4),
        "strict_exact_match": round((total_strict / total_attempted) * 100, 2),
        "normalized_match": round((total_norm / total_attempted) * 100, 2),
        "gold_doc_hit_combined_rate": round((total_combined_hit / total_attempted) * 100, 2),
        "retrieval_intrusion_metrics": {
            "computable_count": len(all_intrusions),
            "na_count": total_attempted - len(all_intrusions),
            "average_retrieval_intrusion_pct": avg_intrusion,
        },
        "qtype_summary": qtype_summary,
        "pipeline_configuration": {
            "mode": "agentic",
            "rag_method": "hybridsearch",
            "pass_qtype": False,
            "graph_name": "Olympics",
        },
    }

    with open(output_summary_path, "w", encoding="utf-8") as f_sum:
        json.dump(summary_report, f_sum, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("      RECOMPUTED PHASE 7 EVIDENCE TELEMETRY & ACCURACY SUMMARY")
    print("=" * 80)
    print(f"Attempted:                       {total_attempted}")
    print(f"HTTP Success Rate:               {total_successful}/{total_attempted} ({total_successful/total_attempted*100:.2f}%)")
    print(f"Strict Exact Match Accuracy:     {total_strict}/{total_attempted} ({summary_report['strict_exact_match']}%)")
    print(f"Normalized Match Accuracy:       {total_norm}/{total_attempted} ({summary_report['normalized_match']}%)")
    print(f"Combined Authoritative Gold Hit: {total_combined_hit}/{total_attempted} ({summary_report['gold_doc_hit_combined_rate']}%)")
    print(f"Retrieval Intrusion at k:        computable={len(all_intrusions)}, N/A={total_attempted - len(all_intrusions)}, mean={avg_intrusion}%")
    print("=" * 80)
    print(f"{'QType':<12} | {'Count':<5} | {'Norm Acc':<12} | {'Chunk Hit':<14} | {'Vertex Hit':<14} | {'Tool Hit':<12} | {'Combined Hit'}")
    print("-" * 80)
    for qt, s in qtype_summary.items():
        cnt = s["attempted"]
        norm_s = f"{s['normalized_match_count']}/{cnt} ({s['normalized_match_pct']}%)"
        chunk_s = f"{s['gold_chunk_hit_count']}/{cnt-s['gold_chunk_na_count']}" if (cnt-s['gold_chunk_na_count']) > 0 else "N/A"
        vertex_s = f"{s['gold_vertex_hit_count']}/{cnt-s['gold_vertex_na_count']}" if (cnt-s['gold_vertex_na_count']) > 0 else "N/A"
        tool_s = f"{s['gold_tool_evidence_hit_count']}/{cnt-s['gold_tool_na_count']}" if (cnt-s['gold_tool_na_count']) > 0 else "N/A"
        comb_s = f"{s['gold_combined_hit_count']}/{cnt} ({s['gold_combined_hit_pct']}%)"
        print(f"{qt:<12} | {cnt:<5} | {norm_s:<12} | {chunk_s:<14} | {vertex_s:<14} | {tool_s:<12} | {comb_s}")
    print("=" * 80)
    print(f"Saved recomputed records to: {output_jsonl_path}")
    print(f"Saved recomputed summary to: {output_summary_path}")


if __name__ == "__main__":
    recompute_benchmark_evidence()
