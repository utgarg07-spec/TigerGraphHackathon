import json
import re
import time
from pathlib import Path
from pyTigerGraph import TigerGraphConnection

def run_phase4_validation(
    config_path: str = "configs/local_server_config.json",
    eval_path: str = "data/eval_public.jsonl",
    output_dir: str = "benchmark/results",
):
    base_dir = Path(__file__).resolve().parent.parent.parent
    cfg_file = base_dir / config_path
    if not cfg_file.exists():
        cfg_file = Path(config_path)

    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)["db_config"]

    conn = TigerGraphConnection(
        host=cfg["hostname"],
        graphname=cfg["graphname"],
        username=cfg["username"],
        password=cfg["password"],
        restppPort=cfg.get("restppPort", "443"),
        gsPort=cfg.get("gsPort", "443"),
    )

    eval_file = base_dir / eval_path
    if not eval_file.exists():
        eval_file = Path(eval_path)

    questions = []
    with open(eval_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    print(f"Loaded {len(questions)} evaluation questions from {eval_file}.")

    # Fetch all Event vertices from TigerGraph DB for direct graph validation
    events_v = conn.getVertices("Event", limit=3000)
    events_by_id = {v["v_id"]: v["attributes"] for v in events_v}
    print(f"Fetched {len(events_by_id)} Event vertices directly from TigerGraph.")

    report_lines = []
    report_lines.append("# Phase 4 — Deterministic Olympic Knowledge Graph Validation Report\n")
    report_lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Event Vertices in TigerGraph: {len(events_by_id)}\n")

    # =========================================================================
    # TASK 4A — GOLD DOCUMENT COVERAGE
    # =========================================================================
    report_lines.append("## Task 4A — Gold Document Coverage\n")
    report_lines.append("| QID | QType | Gold Doc IDs | All Resolved | Sample Event Title |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")

    coverage_passed = True
    coverage_results = []

    for q in questions:
        qid = q["qid"]
        qtype = q["qtype"]
        gold_docs = q.get("gold_doc_ids", [])
        resolved = []
        sample_title = ""
        for gdoc in gold_docs:
            if gdoc in events_by_id:
                resolved.append(gdoc)
                if not sample_title:
                    sample_title = events_by_id[gdoc].get("title", "")
        
        all_ok = (len(resolved) == len(gold_docs))
        if not all_ok:
            coverage_passed = False

        coverage_results.append({
            "qid": qid,
            "qtype": qtype,
            "gold_doc_ids": gold_docs,
            "resolved_count": len(resolved),
            "all_resolved": all_ok
        })
        report_lines.append(f"| {qid} | {qtype} | {', '.join(gold_docs)} | {'PASS' if all_ok else 'FAIL'} | {sample_title[:45]} |")

    cov_pass_cnt = sum(1 for r in coverage_results if r["all_resolved"])
    report_lines.append(f"\nGold Coverage Summary: {cov_pass_cnt} / {len(questions)} PASS\n")

    # =========================================================================
    # TASK 4B — AGGREGATION VALIDATION
    # =========================================================================
    report_lines.append("## Task 4B — Aggregation Question Validation\n")
    report_lines.append("| QID | Question | Gold Answer | Graph Result | Result |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")

    agg_qs = [q for q in questions if q["qtype"] == "aggregation"]
    agg_passed = 0
    agg_results = []

    for q in agg_qs:
        qid = q["qid"]
        question = q["question"]
        gold = str(q["answer"][0]) if isinstance(q["answer"], list) else str(q["answer"])

        m = re.search(r'how many (.*?) events at the (\d{4} (?:Summer|Winter))(?: Olympics)? (?:had|where|with) (?:more than|over) (\d+) competitors', question, re.IGNORECASE)
        if not m:
            m = re.search(r'how many (.*?) events at the (\d{4} (?:Summer|Winter)).*?(\d+) competitors', question, re.IGNORECASE)

        if not m:
            agg_results.append({"qid": qid, "gold": gold, "result": "PARSE_ERROR", "pass": False})
            report_lines.append(f"| {qid} | {question[:40]}... | {gold} | PARSE_ERROR | FAIL |")
            continue

        sport_str = m.group(1).strip().lower()
        games_str = m.group(2).strip().lower()
        thresh = int(m.group(3))

        # Query TigerGraph Event vertices directly
        matched_count = 0
        for attr in events_by_id.values():
            s_name = str(attr.get("sport_name", "")).lower()
            g_name = str(attr.get("games_name", "")).lower()
            comp = int(attr.get("competitors", 0))

            if s_name == sport_str and games_str in g_name and comp > thresh:
                matched_count += 1

        res_str = str(matched_count)
        is_pass = (res_str == gold)
        if is_pass:
            agg_passed += 1

        agg_results.append({"qid": qid, "gold": gold, "result": res_str, "pass": is_pass})
        report_lines.append(f"| {qid} | {question[:45]}... | {gold} | {res_str} | {'PASS' if is_pass else 'FAIL'} |")

    report_lines.append(f"\nAggregation Summary: {agg_passed} / {len(agg_qs)} PASS\n")

    # =========================================================================
    # TASK 4C — SUPERLATIVE VALIDATION
    # =========================================================================
    report_lines.append("## Task 4C — Superlative Question Validation\n")
    report_lines.append("| QID | Question | Gold Answer | Graph Result | Result |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")

    sup_qs = [q for q in questions if q["qtype"] == "superlative"]
    sup_passed = 0
    sup_results = []

    for q in sup_qs:
        qid = q["qid"]
        question = q["question"]
        gold = str(q["answer"][0]) if isinstance(q["answer"], list) else str(q["answer"])

        m = re.search(r'which (.*?) event at the (\d{4} (?:Summer|Winter))(?: Olympics)? (?:had|where|with) the highest number of competitors', question, re.IGNORECASE)
        if not m:
            m = re.search(r'which (.*?) event at the (\d{4} (?:Summer|Winter)).*?highest number of competitors', question, re.IGNORECASE)

        if not m:
            sup_results.append({"qid": qid, "gold": gold, "result": "PARSE_ERROR", "pass": False})
            report_lines.append(f"| {qid} | {question[:40]}... | {gold} | PARSE_ERROR | FAIL |")
            continue

        sport_str = m.group(1).strip().lower()
        games_str = m.group(2).strip().lower()

        matched_events = []
        for attr in events_by_id.values():
            s_name = str(attr.get("sport_name", "")).lower()
            g_name = str(attr.get("games_name", "")).lower()
            if s_name == sport_str and games_str in g_name:
                matched_events.append(attr)

        matched_events.sort(key=lambda x: int(x.get("competitors", 0)), reverse=True)
        top_title = matched_events[0].get("title", "") if matched_events else ""

        is_pass = (top_title == gold)
        if is_pass:
            sup_passed += 1

        sup_results.append({"qid": qid, "gold": gold, "result": top_title, "pass": is_pass})
        report_lines.append(f"| {qid} | {question[:45]}... | {gold} | {top_title} | {'PASS' if is_pass else 'FAIL'} |")

    report_lines.append(f"\nSuperlative Summary: {sup_passed} / {len(sup_qs)} PASS\n")

    # =========================================================================
    # TASK 4D — SPOT CHECKS (5 Lookup, 5 Temporal, 5 Multi-Hop)
    # =========================================================================
    report_lines.append("## Task 4D — Spot Checks (Lookup, Temporal, Multi-Hop)\n")
    report_lines.append("| QID | QType | Question | Gold Answer | Graph Extracted Answer | Result |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    spot_lookup = [q for q in questions if q["qtype"] == "lookup"][:5]
    spot_temp = [q for q in questions if q["qtype"] == "temporal"][:5]
    spot_multihop = [q for q in questions if q["qtype"] == "multi_hop"][:5]

    spot_all = spot_lookup + spot_temp + spot_multihop
    spot_passed = 0

    for q in spot_all:
        qid = q["qid"]
        qtype = q["qtype"]
        question = q["question"]
        gold = str(q["answer"][0]) if isinstance(q["answer"], list) else str(q["answer"])

        # Target doc evaluation
        gold_docs = q.get("gold_doc_ids", [])
        graph_ans = ""
        if gold_docs and gold_docs[0] in events_by_id:
            attr = events_by_id[gold_docs[0]]
            # Extract matching attribute based on gold string match
            for k, val in attr.items():
                if val and str(val).lower() == gold.lower():
                    graph_ans = str(val)
                    break
            if not graph_ans:
                # Check substring or key fields
                if gold.lower() in str(attr.get("gold", "")).lower():
                    graph_ans = attr.get("gold", "")
                elif gold.lower() in str(attr.get("gold_noc", "")).lower():
                    graph_ans = attr.get("gold_noc", "")
                elif str(attr.get("competitors", "")) == gold:
                    graph_ans = str(attr.get("competitors"))
                elif str(attr.get("nations", "")) == gold:
                    graph_ans = str(attr.get("nations"))
                elif str(attr.get("win_value", "")) == gold:
                    graph_ans = str(attr.get("win_value"))
                else:
                    graph_ans = str(attr.get("gold", ""))

        is_pass = (gold.lower() in graph_ans.lower()) or (graph_ans.lower() in gold.lower())
        if is_pass:
            spot_passed += 1

        report_lines.append(f"| {qid} | {qtype} | {question[:40]}... | {gold} | {graph_ans} | {'PASS' if is_pass else 'FAIL'} |")

    report_lines.append(f"\nSpot Check Summary: {spot_passed} / {len(spot_all)} PASS\n")

    # =========================================================================
    # TASK 5 — GRAPH INTEGRITY CHECKS
    # =========================================================================
    report_lines.append("## Task 5 — Graph Integrity Checks\n")
    
    # 1. Primary key check
    dup_ids = len(events_v) - len(events_by_id)
    report_lines.append(f"- **Duplicate Event Primary Keys**: {dup_ids}")

    # 2. Check required identity fields
    missing_title = sum(1 for a in events_by_id.values() if not a.get("title"))
    missing_sport = sum(1 for a in events_by_id.values() if not a.get("sport_name"))
    missing_games = sum(1 for a in events_by_id.values() if not a.get("games_name"))
    report_lines.append(f"- **Event Vertices with Missing Title**: {missing_title}")
    report_lines.append(f"- **Event Vertices with Missing Sport**: {missing_sport}")
    report_lines.append(f"- **Event Vertices with Missing Games**: {missing_games}")

    # 3. Numeric field types check
    invalid_comp = sum(1 for a in events_by_id.values() if not isinstance(a.get("competitors"), int))
    invalid_nat = sum(1 for a in events_by_id.values() if not isinstance(a.get("nations"), int))
    report_lines.append(f"- **Event Vertices with Invalid Competitors Type**: {invalid_comp}")
    report_lines.append(f"- **Event Vertices with Invalid Nations Type**: {invalid_nat}")

    # 4. Fetch Sport, Games, Venue, NOCCountry vertex counts
    sports = conn.getVertices("Sport", limit=5000)
    games = conn.getVertices("Games", limit=5000)
    venues = conn.getVertices("Venue", limit=5000)
    countries = conn.getVertices("NOCCountry", limit=5000)

    report_lines.append(f"- **Total Sport Vertices**: {len(sports)}")
    report_lines.append(f"- **Total Games Vertices**: {len(games)}")
    report_lines.append(f"- **Total Venue Vertices**: {len(venues)}")
    report_lines.append(f"- **Total NOCCountry Vertices**: {len(countries)}")

    out_report_dir = base_dir / output_dir
    out_report_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_report_dir / "phase4_graph_validation_report.md"

    with open(report_file, "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(report_lines) + "\n")

    print(f"\nPhase 4 Validation Report generated at: {report_file}")
    print(f"Aggregation PASS Rate: {agg_passed}/{len(agg_qs)}")
    print(f"Superlative PASS Rate: {sup_passed}/{len(sup_qs)}")
    print(f"Gold Coverage PASS Rate: {cov_pass_cnt}/{len(questions)}")

if __name__ == "__main__":
    run_phase4_validation()
