"""
Benchmark Runner for GraphRAG Evaluation Harness (Phase 2).

No official evaluator was found in the repository; strict_exact_match is the reproducible internal benchmark metric.
Evaluates the GraphRAG /query API against data/eval_public.jsonl without modifying underlying retrieval algorithms or agent logic.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests


def load_local_config(config_path: str = "configs/local_server_config.json") -> Dict[str, Any]:
    """Loads TigerGraph/GraphRAG local server configuration."""
    cfg_file = Path(config_path)
    if not cfg_file.exists():
        cfg_file = Path("configs/server_config.json")
    if not cfg_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(cfg_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_olympic_doc_ids(events_path: str = "data/processed/events.jsonl") -> set:
    """Loads the set of verified Olympic-event doc_ids for intrusion calculation."""
    events_file = Path(events_path)
    if not events_file.exists():
        print(f"Warning: {events_path} not found. Intrusion metrics will be disabled.")
        return set()
    
    olympic_ids = set()
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("doc_id"):
                olympic_ids.add(rec["doc_id"].upper())
    return olympic_ids


def load_evaluation_dataset(eval_path: str = "data/eval_public.jsonl") -> List[Dict[str, Any]]:
    """Loads and validates evaluation dataset records."""
    eval_file = Path(eval_path)
    if not eval_file.exists():
        raise FileNotFoundError(f"Evaluation file not found: {eval_path}")

    records = []
    qids = set()
    duplicate_qids = []
    missing_answers = []

    with open(eval_file, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            qid = rec.get("qid")
            if qid in qids:
                duplicate_qids.append(qid)
            else:
                qids.add(qid)
            
            ans = rec.get("answer")
            if ans is None or ans == "" or (isinstance(ans, list) and len(ans) == 0):
                missing_answers.append(qid)
                
            records.append(rec)

    if duplicate_qids:
        raise ValueError(f"Data Integrity Error: Duplicate QIDs found in {eval_path}: {duplicate_qids}")
    if missing_answers:
        raise ValueError(f"Data Integrity Error: Missing gold answers found in {eval_path}: {missing_answers}")

    return records


def extract_retrieval_info(query_sources: Dict[str, Any], olympic_doc_ids: set) -> Tuple[List[str], List[str], Optional[float]]:
    """
    Extracts retrieved chunk IDs, source document IDs, and calculates retrieval_intrusion_at_k.
    """
    from benchmark.evidence_evaluator import extract_evidence_from_payload
    ev = extract_evidence_from_payload(
        query_sources=query_sources,
        agent_steps=query_sources.get("agent_steps", []) if isinstance(query_sources, dict) else [],
        citations=query_sources.get("citations", []) if isinstance(query_sources, dict) else [],
        olympic_doc_ids=olympic_doc_ids,
    )
    return ev["retrieved_chunk_ids"], ev["retrieved_doc_ids"], ev["retrieval_intrusion_at_k"]


def normalize_answer_string(s: str) -> str:
    """Normalize answer string for robust comparison:
    - Strips markdown formatting (*, _, `, #)
    - Lowercases
    - Normalizes punctuation, hyphens, and unicode dashes (\u2013, \u2014) to standard space/hyphen
    - Replaces number words (zero-twenty) with integer digits
    - Normalizes common event and season suffixes/variants
    - Collapses whitespace
    """
    if not s or not isinstance(s, str):
        return ""
    
    text = s.lower()
    text = re.sub(r'[*_`#~]', '', text)
    text = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015]', '-', text)
    
    number_map = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20"
    }
    for word, digit in number_map.items():
        text = re.sub(rf'\b{word}\b', digit, text)

    # Clean punctuation except alphanumeric and hyphen
    text = re.sub(r'[^\w\s\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def compute_normalized_match(pred_str: str, target_gold: str) -> bool:
    """
    Diagnostic matching rule:
    - Normalizes markdown, numbers, dashes, punctuation, and whitespace
    - Checks whether canonical gold answer occurs as substring or token sequence in prediction
    """
    if not pred_str or not target_gold:
        return False
    
    clean_pred = normalize_answer_string(pred_str)
    clean_gold = normalize_answer_string(target_gold)
    
    if not clean_gold:
        return False
        
    if clean_gold in clean_pred:
        return True
        
    # Also check without hyphens
    pred_no_hyphen = clean_pred.replace("-", " ")
    gold_no_hyphen = clean_gold.replace("-", " ")
    pred_no_hyphen = re.sub(r'\s+', ' ', pred_no_hyphen).strip()
    gold_no_hyphen = re.sub(r'\s+', ' ', gold_no_hyphen).strip()
    
    return gold_no_hyphen in pred_no_hyphen


def run_benchmark(
    eval_path: str = "data/eval_public.jsonl",
    graph_name: str = "Olympics",
    base_url: str = "http://localhost:8000",
    mode: str = "classic",
    rag_method: str = "similaritysearch",
    pass_qtype: bool = False,
    selected_qid: Optional[str] = None,
    selected_qtype: Optional[str] = None,
    limit: Optional[int] = None,
    run_name: str = "smoke_test",
    output_dir: str = "benchmark/results",
) -> Dict[str, Any]:
    """
    Executes benchmark runner over specified evaluation questions.
    """
    cfg = load_local_config()
    db_cfg = cfg.get("db_config", {})
    username = db_cfg.get("username", "__GSQL__secret")
    password = db_cfg.get("password", "")

    auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/json",
    }

    olympic_doc_ids = load_olympic_doc_ids()
    eval_records = load_evaluation_dataset(eval_path)

    filtered_records = []
    for rec in eval_records:
        if selected_qid and rec["qid"] != selected_qid:
            continue
        if selected_qtype and rec["qtype"] != selected_qtype:
            continue
        filtered_records.append(rec)

    if limit is not None and limit > 0:
        filtered_records = filtered_records[:limit]

    print(f"Starting benchmark run '{run_name}' with {len(filtered_records)} questions...")
    print(f"Configuration: mode={mode}, rag_method={rag_method}, pass_qtype={pass_qtype}\n")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    jsonl_output_path = Path(output_dir) / f"{run_name}.jsonl"
    summary_output_path = Path(output_dir) / f"{run_name}_summary.json"

    completed_qids = set()
    results = []

    # Checkpoint loading: if output jsonl exists, load already completed records
    if jsonl_output_path.exists():
        with open(jsonl_output_path, "r", encoding="utf-8") as f_prev:
            for line in f_prev:
                if line.strip():
                    try:
                        rec_prev = json.loads(line)
                        if rec_prev.get("error") is None:
                            completed_qids.add(rec_prev["qid"])
                            results.append(rec_prev)
                    except Exception:
                        pass
        print(f"Resuming benchmark run '{run_name}': {len(completed_qids)} already completed questions loaded.")

    qtype_counts = {}
    qtype_strict = {}
    qtype_norm = {}
    qtype_gold_hit = {}

    for r in results:
        qt = r["qtype"]
        if qt not in qtype_counts:
            qtype_counts[qt] = 0
            qtype_strict[qt] = 0
            qtype_norm[qt] = 0
            qtype_gold_hit[qt] = 0
        qtype_counts[qt] += 1
        if r.get("strict_exact_match"):
            qtype_strict[qt] += 1
        if r.get("normalized_match"):
            qtype_norm[qt] += 1
        if r.get("gold_doc_hit"):
            qtype_gold_hit[qt] += 1

    target_url = f"{base_url.rstrip('/')}/{graph_name}/query"

    with open(jsonl_output_path, "a", encoding="utf-8") as f_out:
        for idx, rec in enumerate(filtered_records, 1):
            qid = rec["qid"]
            question = rec["question"]
            qtype = rec["qtype"]
            gold_answers = rec.get("answer", [])
            gold_str = gold_answers[0] if isinstance(gold_answers, list) and len(gold_answers) > 0 else str(gold_answers)
            gold_doc_ids = rec.get("gold_doc_ids", [])

            if qid in completed_qids:
                print(f"[{idx:03d}/{len(filtered_records)}] QID: {qid} ({qtype:12s}) | SKIPPED (Already completed)")
                continue

            payload = {
                "query": question,  # Preserve natural language question untouched
                "mode": mode,
                "rag_method": rag_method,
                "include_fields": ["all"],
            }
            if pass_qtype:
                payload["qtype"] = qtype

            start_time = time.time()
            prediction = ""
            error_info = None
            resp_data = {}

            try:
                response = requests.post(target_url, json=payload, headers=headers, timeout=180)
                latency = round(time.time() - start_time, 3)

                if response.status_code == 200:
                    resp_data = response.json()
                    prediction = resp_data.get("natural_language_response", "")
                else:
                    error_info = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                latency = round(time.time() - start_time, 3)
                error_info = f"Request Exception: {str(e)}"

            # Scoring:
            # 1. Primary Metric: strict_exact_match (exact string equality after trimming whitespace)
            norm_pred = prediction.strip() if prediction else ""
            norm_gold = gold_str.strip() if gold_str else ""
            strict_exact_match = (norm_pred == norm_gold)

            # 2. Diagnostic Metric: normalized_match
            normalized_match = compute_normalized_match(prediction, gold_str)

            query_sources = resp_data.get("query_sources", {}) if isinstance(resp_data, dict) else {}
            token_usage = query_sources.get("token_usage") if isinstance(query_sources, dict) else None
            citations = query_sources.get("citations") if isinstance(query_sources, dict) else None
            agent_steps = query_sources.get("agent_steps") if isinstance(query_sources, dict) else None
            
            plan = None
            if isinstance(agent_steps, list):
                for step in agent_steps:
                    if isinstance(step, dict) and step.get("node") == "plan_question":
                        plan = step.get("output")

            from benchmark.evidence_evaluator import extract_evidence_from_payload, evaluate_gold_evidence
            ev_dict = extract_evidence_from_payload(
                query_sources=query_sources,
                agent_steps=agent_steps,
                citations=citations,
                olympic_doc_ids=olympic_doc_ids,
            )
            chunk_ids = ev_dict["retrieved_chunk_ids"]
            doc_ids = ev_dict["retrieved_doc_ids"]
            intrusion_pct = ev_dict["retrieval_intrusion_at_k"]

            # 3. Multi-category Gold Doc Hit calculation
            gold_eval = evaluate_gold_evidence(
                evidence=ev_dict,
                gold_doc_ids=gold_doc_ids,
                qtype=qtype,
                error=error_info,
            )
            gold_hit = gold_eval["gold_hit_combined"]

            # Extract provider information if present
            provider_routed = None
            if isinstance(query_sources, dict):
                provider_routed = query_sources.get("provider") or query_sources.get("provider_used")
            if not provider_routed and isinstance(token_usage, dict):
                provider_routed = token_usage.get("provider")

            result_record = {
                "qid": qid,
                "qtype": qtype,
                "question": question,
                "prediction": prediction,
                "gold": gold_str,
                "gold_doc_ids": gold_doc_ids,
                "strict_exact_match": strict_exact_match,
                "normalized_match": normalized_match,
                "gold_doc_hit": gold_hit,
                "correct": strict_exact_match or normalized_match,
                "latency": latency,
                "token_usage": token_usage,
                "provider": provider_routed,
                "retrieved_chunk_ids": chunk_ids,
                "retrieved_doc_ids": doc_ids,
                "retrieval_intrusion_at_k": intrusion_pct,
                "citations": citations,
                "agent_steps": agent_steps,
                "plan": plan,
                "error": error_info,
            }

            f_out.write(json.dumps(result_record, ensure_ascii=False) + "\n")
            f_out.flush()
            results.append(result_record)
            completed_qids.add(qid)

            if qtype not in qtype_counts:
                qtype_counts[qtype] = 0
                qtype_strict[qtype] = 0
                qtype_norm[qtype] = 0
                qtype_gold_hit[qtype] = 0
            qtype_counts[qtype] += 1
            if strict_exact_match:
                qtype_strict[qtype] += 1
            if normalized_match:
                qtype_norm[qtype] += 1
            if gold_hit:
                qtype_gold_hit[qtype] += 1

            status_str = "EXACT_MATCH" if strict_exact_match else ("NORM_MATCH" if normalized_match else "FAIL")
            gold_str_disp = "GOLD_HIT" if gold_hit else "GOLD_MISS"
            err_str = f" [ERROR: {error_info}]" if error_info else ""
            print(f"[{idx:03d}/{len(filtered_records)}] QID: {qid} | QType: {qtype:12s} | Result: {status_str:11s} | GoldDoc: {gold_str_disp:9s} | Latency: {latency:6.2f}s{err_str}")

            # Pace requests
            elapsed = time.time() - start_time
            sleep_needed = max(0.0, 5.0 - elapsed)
            time.sleep(sleep_needed)

    total_attempted = len(results)
    total_successful = sum(1 for r in results if r.get("error") is None)
    total_failed = sum(1 for r in results if r.get("error") is not None)
    
    total_strict_correct = sum(1 for r in results if r.get("strict_exact_match"))
    strict_accuracy = round((total_strict_correct / total_attempted) * 100, 2) if total_attempted > 0 else 0.0

    total_norm_correct = sum(1 for r in results if r.get("normalized_match"))
    norm_accuracy = round((total_norm_correct / total_attempted) * 100, 2) if total_attempted > 0 else 0.0

    total_gold_hits = sum(1 for r in results if r.get("gold_doc_hit"))
    gold_hit_rate = round((total_gold_hits / total_attempted) * 100, 2) if total_attempted > 0 else 0.0

    http_success_rate = round((total_successful / total_attempted), 4) if total_attempted > 0 else 0.0
    avg_latency = round(sum(r.get("latency", 0) for r in results) / total_attempted, 3) if total_attempted > 0 else 0.0
    
    intrusions = [r.get("retrieval_intrusion_at_k") for r in results if r.get("retrieval_intrusion_at_k") is not None]
    avg_intrusion = round(sum(intrusions) / len(intrusions), 2) if intrusions else None

    qtype_summary = {}
    for qt, count in qtype_counts.items():
        s_cnt = qtype_strict[qt]
        n_cnt = qtype_norm[qt]
        g_cnt = qtype_gold_hit[qt]
        qtype_summary[qt] = {
            "attempted": count,
            "strict_exact_match_count": s_cnt,
            "strict_exact_match_pct": round((s_cnt / count) * 100, 2),
            "normalized_match_count": n_cnt,
            "normalized_match_pct": round((n_cnt / count) * 100, 2),
            "gold_doc_hit_count": g_cnt,
            "gold_doc_hit_pct": round((g_cnt / count) * 100, 2),
        }

    summary_report = {
        "run_name": run_name,
        "number_attempted": total_attempted,
        "number_successful": total_successful,
        "number_failed": total_failed,
        "http_success_rate": http_success_rate,
        "strict_exact_match": strict_accuracy,
        "normalized_match": norm_accuracy,
        "gold_doc_hit_rate": gold_hit_rate,
        "avg_latency_seconds": avg_latency,
        "average_retrieval_intrusion_pct": avg_intrusion,
        "qtype_summary": qtype_summary,
        "pipeline_configuration": {
            "mode": mode,
            "rag_method": rag_method,
            "pass_qtype": pass_qtype,
            "graph_name": graph_name,
        },
    }

    with open(summary_output_path, "w", encoding="utf-8") as f_sum:
        json.dump(summary_report, f_sum, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("BENCHMARK RUN SUMMARY")
    print("=" * 60)
    print(f"Run Name:            {run_name}")
    print(f"Attempted:           {total_attempted}")
    print(f"HTTP Success Rate:   {http_success_rate * 100:.2f}% ({total_successful}/{total_attempted})")
    print(f"strict_exact_match:  {total_strict_correct} / {total_attempted} ({strict_accuracy}%)")
    print(f"normalized_match:    {total_norm_correct} / {total_attempted} ({norm_accuracy}%)")
    print(f"gold_doc_hit_rate:   {total_gold_hits} / {total_attempted} ({gold_hit_rate}%)")
    print(f"Avg Latency Seconds: {avg_latency}s")
    print(f"Average Intrusion:   {avg_intrusion}%" if avg_intrusion is not None else "Average Intrusion: N/A")
    print("\nAccuracy & Gold Doc Hit Rate by QType:")
    for qt, stats in qtype_summary.items():
        print(f"  - {qt:20s}: norm={stats['normalized_match_count']}/{stats['attempted']} ({stats['normalized_match_pct']}%) | gold_hit={stats['gold_doc_hit_count']}/{stats['attempted']} ({stats['gold_doc_hit_pct']}%) | strict={stats['strict_exact_match_count']}/{stats['attempted']} ({stats['strict_exact_match_pct']}%)")
    print("=" * 60)
    print(f"Detailed results: {jsonl_output_path}")
    print(f"Summary report:   {summary_output_path}")
    print("=" * 60)

    return summary_report


def main():
    parser = argparse.ArgumentParser(description="GraphRAG Benchmark Runner (Phase 2)")
    parser.add_argument("--all", action="store_true", help="Run all questions in dataset")
    parser.add_argument("--qid", type=str, default=None, help="Run specific QID (e.g. pub-001)")
    parser.add_argument("--qtype", type=str, default=None, help="Filter by qtype (e.g. aggregation)")
    parser.add_argument("--limit", type=int, default=None, help="Limit max questions to process")
    parser.add_argument("--mode", type=str, default="classic", choices=["classic", "agentic"], help="Query mode")
    parser.add_argument("--rag-method", type=str, default="similaritysearch", choices=["similaritysearch", "hybridsearch"], help="RAG method")
    parser.add_argument("--pass-qtype", action="store_true", help="Pass qtype field in POST payload to /query")
    parser.add_argument("--run-name", type=str, default="smoke_test", help="Custom name for benchmark run output files")

    args = parser.parse_args()

    run_benchmark(
        mode=args.mode,
        rag_method=args.rag_method,
        pass_qtype=args.pass_qtype,
        selected_qid=args.qid,
        selected_qtype=args.qtype,
        limit=args.limit,
        run_name=args.run_name,
    )


if __name__ == "__main__":
    main()
