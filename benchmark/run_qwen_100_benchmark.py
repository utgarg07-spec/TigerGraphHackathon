import json
import time
import base64
import requests
import re
from pathlib import Path
from typing import Dict, Any, List

CONFIG_PATH = "configs/local_server_config.json"
EVAL_PATH = "data/eval_public.jsonl"
EVENTS_PATH = "data/processed/events.jsonl"
OUTPUT_DIR = "benchmark/results"

def load_local_config(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_olympic_doc_ids(events_path: str = EVENTS_PATH) -> set:
    events_file = Path(events_path)
    if not events_file.exists():
        return set()
    olympic_ids = set()
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("doc_id"):
                olympic_ids.add(rec["doc_id"].upper())
    return olympic_ids

def load_evaluation_dataset(eval_path: str = EVAL_PATH) -> List[Dict[str, Any]]:
    with open(eval_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def compute_normalized_match(pred_str: str, target_gold: str) -> bool:
    if not pred_str or not target_gold:
        return False
    clean_pred = re.sub(r'\*\*|\*|__', '', pred_str).lower()
    clean_gold = re.sub(r'\*\*|\*|__', '', target_gold).lower()
    return clean_gold in clean_pred

def extract_retrieval_info(query_sources: Dict[str, Any], olympic_doc_ids: set):
    if not query_sources or not isinstance(query_sources, dict):
        return [], [], None

    agent_steps = query_sources.get("agent_steps", [])
    retrieved_chunk_ids = []

    for step in agent_steps:
        if not isinstance(step, dict):
            continue
        output_str = step.get("output", "")
        if not output_str or not isinstance(output_str, str):
            continue
        try:
            output_json = json.loads(output_str)
            ctx = output_json.get("context", {})
            if isinstance(ctx, dict):
                res = ctx.get("result", {})
                if isinstance(res, dict):
                    fin_ret = res.get("final_retrieval", {})
                    if isinstance(fin_ret, dict):
                        retrieved_chunk_ids.extend(list(fin_ret.keys()))
        except Exception:
            pass

    if not retrieved_chunk_ids:
        qs_str = json.dumps(query_sources)
        matches = re.findall(r'"([Qq]\d+_chunk_\d+)"', qs_str)
        retrieved_chunk_ids = list(set(matches))

    doc_id_set = set()
    for chunk_id in retrieved_chunk_ids:
        match = re.match(r'^([Qq]\d+)_chunk_', chunk_id)
        if match:
            doc_id = match.group(1).upper()
            doc_id_set.add(doc_id)

    retrieved_doc_ids = sorted(list(doc_id_set))
    intrusion_pct = None
    if retrieved_doc_ids and olympic_doc_ids:
        non_olympic_count = sum(1 for d in retrieved_doc_ids if d not in olympic_doc_ids)
        intrusion_pct = round((non_olympic_count / len(retrieved_doc_ids)) * 100, 2)

    return retrieved_chunk_ids, retrieved_doc_ids, intrusion_pct

def main():
    print("==================================================")
    print("PHASE 3 — FINAL 100-QUESTION QWEN BENCHMARK RUNNER")
    print("==================================================")

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
    records = load_evaluation_dataset()

    target_url = "http://localhost:8000/Olympics/query"
    run_name = "phase3_qwen_100_benchmark"
    jsonl_output_path = Path(OUTPUT_DIR) / f"{run_name}.jsonl"
    summary_output_path = Path(OUTPUT_DIR) / f"{run_name}_summary.json"

    print(f"Executing benchmark over {len(records)} public questions...")
    print(f"Mode: classic | RAG Method: similaritysearch | pass_qtype: False\n")

    results = []
    qtype_stats = {}

    with open(jsonl_output_path, "w", encoding="utf-8") as f_out:
        for idx, rec in enumerate(records, 1):
            qid = rec["qid"]
            question = rec["question"]
            qtype = rec["qtype"]
            gold_answers = rec.get("answer", [])
            gold_str = gold_answers[0] if isinstance(gold_answers, list) and len(gold_answers) > 0 else str(gold_answers)
            gold_doc_ids = rec.get("gold_doc_ids", [])

            payload = {
                "query": question,
                "mode": "classic",
                "rag_method": "similaritysearch",
                "include_fields": ["all"]
            }

            start_time = time.time()
            prediction = ""
            error_info = None
            resp_data = {}

            # Retries for API calls
            for attempt in range(3):
                try:
                    response = requests.post(target_url, json=payload, headers=headers, timeout=180)
                    latency = round(time.time() - start_time, 3)
                    if response.status_code == 200:
                        resp_data = response.json()
                        prediction = resp_data.get("natural_language_response", "")
                        error_info = None
                        break
                    else:
                        error_info = f"HTTP {response.status_code}: {response.text}"
                        if response.status_code in [429, 503]:
                            time.sleep(5)
                except Exception as e:
                    latency = round(time.time() - start_time, 3)
                    error_info = f"Request Exception: {str(e)}"
                    time.sleep(2)

            norm_pred = prediction.strip() if prediction else ""
            norm_gold = gold_str.strip() if gold_str else ""
            strict_exact_match = (norm_pred == norm_gold)
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

            chunk_ids, doc_ids, intrusion_pct = extract_retrieval_info(query_sources, olympic_doc_ids)

            # Check gold doc retrieval hit
            gold_hit = any(g_doc.upper() in [d.upper() for d in doc_ids] for g_doc in gold_doc_ids)

            # Separate latencies if available in agent steps
            retrieval_lat_s = 0.0
            gen_lat_s = 0.0
            if isinstance(agent_steps, list):
                for step in agent_steps:
                    if isinstance(step, dict):
                        if step.get("node") == "supportai":
                            retrieval_lat_s = step.get("duration_s", 0.0)
                        elif step.get("node") == "generate_answer":
                            gen_lat_s = step.get("duration_s", 0.0)

            result_record = {
                "qid": qid,
                "qtype": qtype,
                "question": question,
                "prediction": prediction,
                "gold": gold_str,
                "gold_doc_ids": gold_doc_ids,
                "strict_exact_match": strict_exact_match,
                "normalized_match": normalized_match,
                "correct": strict_exact_match,
                "gold_retrieval_hit": gold_hit,
                "latency": latency,
                "retrieval_latency_s": retrieval_lat_s,
                "gen_latency_s": gen_lat_s,
                "token_usage": token_usage,
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

            if qtype not in qtype_stats:
                qtype_stats[qtype] = {
                    "count": 0,
                    "strict_match": 0,
                    "norm_match": 0,
                    "gold_hit": 0,
                    "latencies": [],
                    "retrieval_latencies": [],
                    "gen_latencies": []
                }

            st = qtype_stats[qtype]
            st["count"] += 1
            if strict_exact_match:
                st["strict_match"] += 1
            if normalized_match:
                st["norm_match"] += 1
            if gold_hit:
                st["gold_hit"] += 1
            st["latencies"].append(latency)
            if retrieval_lat_s:
                st["retrieval_latencies"].append(retrieval_lat_s)
            if gen_lat_s:
                st["gen_latencies"].append(gen_lat_s)

            status_str = "EXACT_MATCH" if strict_exact_match else ("NORM_MATCH" if normalized_match else "FAIL")
            err_str = f" [ERROR: {error_info}]" if error_info else ""
            hit_str = "GOLD_HIT" if gold_hit else "GOLD_MISS"
            print(f"[{idx:3d}/100] QID: {qid:8s} | Type: {qtype:12s} | Result: {status_str:11s} | {hit_str:9s} | Latency: {latency:6.2f}s{err_str}", flush=True)

            time.sleep(1.0) # Rate limit mitigation

    # Summary calculations
    total_q = len(results)
    strict_count = sum(1 for r in results if r["strict_exact_match"])
    norm_count = sum(1 for r in results if r["normalized_match"])
    gold_hit_count = sum(1 for r in results if r["gold_retrieval_hit"])
    error_count = sum(1 for r in results if r["error"] is not None)

    strict_acc = round((strict_count / total_q) * 100, 2)
    norm_acc = round((norm_count / total_q) * 100, 2)
    gold_hit_rate = round((gold_hit_count / total_q) * 100, 2)
    avg_latency = round(sum(r["latency"] for r in results) / total_q, 3)

    summary_data = {
        "run_name": run_name,
        "total_questions": total_q,
        "http_success_count": total_q - error_count,
        "http_failure_count": error_count,
        "strict_exact_match_count": strict_count,
        "strict_exact_match_accuracy_pct": strict_acc,
        "normalized_match_count": norm_count,
        "normalized_match_accuracy_pct": norm_acc,
        "gold_retrieval_hit_count": gold_hit_count,
        "gold_retrieval_hit_rate_pct": gold_hit_rate,
        "avg_latency_s": avg_latency,
        "qtype_breakdown": {}
    }

    for qt, st in qtype_stats.items():
        cnt = st["count"]
        summary_data["qtype_breakdown"][qt] = {
            "count": cnt,
            "strict_match_count": st["strict_match"],
            "strict_match_pct": round((st["strict_match"] / cnt) * 100, 2),
            "norm_match_count": st["norm_match"],
            "norm_match_pct": round((st["norm_match"] / cnt) * 100, 2),
            "gold_hit_count": st["gold_hit"],
            "gold_hit_rate_pct": round((st["gold_hit"] / cnt) * 100, 2),
            "avg_latency_s": round(sum(st["latencies"]) / cnt, 3),
            "avg_retrieval_latency_s": round(sum(st["retrieval_latencies"]) / len(st["retrieval_latencies"]), 3) if st["retrieval_latencies"] else 0,
            "avg_gen_latency_s": round(sum(st["gen_latencies"]) / len(st["gen_latencies"]), 3) if st["gen_latencies"] else 0
        }

    with open(summary_output_path, "w", encoding="utf-8") as f_sum:
        json.dump(summary_data, f_sum, indent=2)

    print("\n==================================================")
    print("BENCHMARK RUN SUMMARY")
    print("==================================================")
    print(f"Total Questions:                     {total_q}")
    print(f"Strict Exact Match Accuracy:         {strict_acc}% ({strict_count}/{total_q})")
    print(f"Normalized Match Accuracy:           {norm_acc}% ({norm_count}/{total_q})")
    print(f"Gold Document Retrieval Hit Rate:    {gold_hit_rate}% ({gold_hit_count}/{total_q})")
    print(f"Average Total Latency:               {avg_latency} s")
    print(f"HTTP Errors / Failures:              {error_count}")
    print("\nBreakdown by Question Type:")
    for qt, b in summary_data["qtype_breakdown"].items():
        print(f"  {qt:12s} | Strict: {b['strict_match_pct']:5.2f}% | Norm: {b['norm_match_pct']:5.2f}% | Gold Hit: {b['gold_hit_rate_pct']:5.2f}% | Latency: {b['avg_latency_s']}s")

if __name__ == "__main__":
    main()
