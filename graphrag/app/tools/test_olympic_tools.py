# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# Independent Standalone Test Suite for Phase 6 Deterministic Olympic Tools

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pyTigerGraph import TigerGraphConnection

# Ensure tools module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.olympic_tools import (
    graphrag__lookup,
    graphrag__aggregate,
    graphrag__superlative,
    graphrag__temporal_resolve,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_olympic_tools")


class StandaloneCtx:
    """Mock context object wrapping TigerGraph connection for tool calls."""
    def __init__(self, conn):
        self.conn = conn


def run_phase6_standalone_tests():
    # Load TigerGraph Connection
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "local_server_config.json")
    if not os.path.exists(cfg_path):
        cfg_path = "configs/local_server_config.json"

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)["db_config"]

    conn = TigerGraphConnection(
        host=cfg["hostname"],
        graphname=cfg["graphname"],
        username=cfg["username"],
        password=cfg["password"],
        restppPort=cfg["restppPort"],
        gsPort=cfg["gsPort"],
    )
    conn.getToken()
    ctx = StandaloneCtx(conn)

    # Load public evaluation dataset
    eval_candidates = [
        "data/eval_public.jsonl",
        "/code/data/eval_public.jsonl",
        "../../data/eval_public.jsonl",
        "../data/eval_public.jsonl"
    ]
    eval_path = None
    for cand in eval_candidates:
        if os.path.exists(cand):
            eval_path = cand
            break
    if not eval_path:
        raise FileNotFoundError("Could not find data/eval_public.jsonl")

    with open(eval_path, "r", encoding="utf-8") as f:
        eval_data = [json.loads(line) for line in f]

    print("==========================================================================")
    print("        PHASE 6 — DETERMINISTIC OLYMPIC TOOL LAYER TEST SUITE            ")
    print("==========================================================================")

    # --------------------------------------------------------------------------
    # 1. TOOL 1: graphrag__lookup
    # --------------------------------------------------------------------------
    lookup_questions = [x for x in eval_data if x.get("qtype") == "lookup"]
    print(f"\n--- 1. TESTING graphrag__lookup ({len(lookup_questions)} Known-Answer Public Questions) ---")
    
    lookup_passed = 0
    lookup_failed = 0
    lookup_failures = []

    for item in lookup_questions:
        qid = item["qid"]
        q = item["question"]
        gold = item["answer"][0]

        # Extract title from question
        prefix = "How many nations competed in "
        event_title = q
        if q.startswith(prefix):
            event_title = q[len(prefix):].rstrip("?").strip()

        args = {"event_title": event_title}
        res = graphrag__lookup(ctx, event_title)
        
        ret_val = res.get("summary") if res.get("ok") else "NO_RESULT"
        is_pass = res.get("ok") and (str(ret_val) == str(gold))

        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            lookup_passed += 1
        else:
            lookup_failed += 1
            lookup_failures.append({
                "qid": qid,
                "args": args,
                "ret": ret_val,
                "expected": gold,
                "reason": f"Tool returned {ret_val}, expected {gold}"
            })

        print(f"[{status}] QID: {qid}")
        print(f"  Q: {q}")
        print(f"  Args: {args}")
        print(f"  Result: {ret_val} | Expected: {gold}")

    # --------------------------------------------------------------------------
    # 2. TOOL 2: graphrag__aggregate
    # --------------------------------------------------------------------------
    agg_questions = [x for x in eval_data if x.get("qtype") == "aggregation"]
    print(f"\n--- 2. TESTING graphrag__aggregate ({len(agg_questions)} Known-Answer Public Questions) ---")

    agg_passed = 0
    agg_failed = 0
    agg_failures = []

    for item in agg_questions:
        qid = item["qid"]
        q = item["question"]
        gold = item["answer"][0]

        m = re.search(r"how many (.*?) events at the (.*?) had more than (\d+) competitors\?", q, re.IGNORECASE)
        if not m:
            agg_failed += 1
            agg_failures.append({"qid": qid, "args": {}, "ret": "PARSE_ERROR", "expected": gold, "reason": "Regex question parse failed"})
            continue

        sport = m.group(1).strip()
        games = m.group(2).strip()
        thresh = int(m.group(3))

        args = {"sport": sport, "games": games, "threshold": thresh}
        res = graphrag__aggregate(ctx, sport, games, thresh)

        ret_val = res.get("summary") if res.get("ok") else "NO_RESULT"
        is_pass = res.get("ok") and (str(ret_val) == str(gold))

        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            agg_passed += 1
        else:
            agg_failed += 1
            agg_failures.append({
                "qid": qid,
                "args": args,
                "ret": ret_val,
                "expected": gold,
                "reason": f"Tool returned {ret_val}, expected {gold}"
            })

        print(f"[{status}] QID: {qid}")
        print(f"  Q: {q}")
        print(f"  Args: {args}")
        print(f"  Result: {ret_val} | Expected: {gold}")

    # --------------------------------------------------------------------------
    # 3. TOOL 3: graphrag__superlative
    # --------------------------------------------------------------------------
    sup_questions = [x for x in eval_data if x.get("qtype") == "superlative"]
    print(f"\n--- 3. TESTING graphrag__superlative ({len(sup_questions)} Known-Answer Public Questions) ---")

    sup_passed = 0
    sup_failed = 0
    sup_failures = []

    for item in sup_questions:
        qid = item["qid"]
        q = item["question"]
        gold = item["answer"][0]

        m = re.search(r"which (.*?) event at the (.*?) had the highest number of competitors\?", q, re.IGNORECASE)
        if not m:
            sup_failed += 1
            sup_failures.append({"qid": qid, "args": {}, "ret": "PARSE_ERROR", "expected": gold, "reason": "Regex question parse failed"})
            continue

        sport = m.group(1).strip()
        games = m.group(2).strip()

        args = {"sport": sport, "games": games}
        res = graphrag__superlative(ctx, sport, games)

        ret_val = res.get("summary") if res.get("ok") else "NO_RESULT"
        is_pass = res.get("ok") and (str(ret_val) == str(gold))

        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            sup_passed += 1
        else:
            sup_failed += 1
            sup_failures.append({
                "qid": qid,
                "args": args,
                "ret": ret_val,
                "expected": gold,
                "reason": f"Tool returned {ret_val}, expected {gold}"
            })

        print(f"[{status}] QID: {qid}")
        print(f"  Q: {q}")
        print(f"  Args: {args}")
        print(f"  Result: {ret_val} | Expected: {gold}")

    # --------------------------------------------------------------------------
    # 4. TOOL 4: graphrag__temporal_resolve
    # --------------------------------------------------------------------------
    temp_questions = [x for x in eval_data if x.get("qtype") == "temporal"]
    print(f"\n--- 4. TESTING graphrag__temporal_resolve ({len(temp_questions)} Known-Answer Public Questions) ---")

    temp_passed = 0
    temp_failed = 0
    temp_failures = []

    for item in temp_questions:
        qid = item["qid"]
        q = item["question"]
        gold = item["answer"][0]

        m = re.search(r"Who won the gold medal in the (.*?) event at the (Summer|Winter) Olympics held (immediately before|immediately after) (\d{4})\?", q)
        if not m:
            temp_failed += 1
            temp_failures.append({"qid": qid, "args": {}, "ret": "PARSE_ERROR", "expected": gold, "reason": "Regex question parse failed"})
            continue

        raw_ev = m.group(1).strip()
        season = m.group(2).strip()
        direction = m.group(3).strip()
        ref_year = int(m.group(4))

        args = {"event_name": raw_ev, "season": season, "reference_year": ref_year, "direction": direction}
        res = graphrag__temporal_resolve(ctx, raw_ev, season, ref_year, direction)

        ret_val = res.get("summary") if res.get("ok") else "NO_RESULT"
        
        # TASK 4 Data Fidelity Verification (Byte-for-byte equivalence)
        byte_exact = False
        if res.get("ok") and isinstance(ret_val, str):
            byte_exact = (ret_val.encode('utf-8') == gold.encode('utf-8'))

        is_pass = res.get("ok") and byte_exact

        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            temp_passed += 1
        else:
            temp_failed += 1
            temp_failures.append({
                "qid": qid,
                "args": args,
                "ret": ret_val,
                "expected": gold,
                "reason": f"Byte-for-byte exact match failed. Returned '{ret_val}', expected '{gold}'"
            })

        print(f"[{status}] QID: {qid}")
        print(f"  Q: {q}")
        print(f"  Args: {args}")
        print(f"  Result: '{ret_val}' | Expected: '{gold}' | ByteExact: {byte_exact}")

    # --------------------------------------------------------------------------
    # 5. TASK 3: ADDITIONAL EDGE-CASE TESTS
    # --------------------------------------------------------------------------
    print("\n--- 5. TESTING ADDITIONAL EDGE-CASES (TASK 3) ---")
    edge_passed = 0
    edge_failed = 0

    # Edge Case 1: Nonexistent event title
    e1_res = graphrag__lookup(ctx, "Underwater Hockey at 1800 Olympics")
    e1_pass = not e1_res.get("ok")
    print(f"[{'PASS' if e1_pass else 'FAIL'}] Edge 1 (Nonexistent Title): ok={e1_res.get('ok')} | Summary: {e1_res.get('summary')}")
    if e1_pass: edge_passed += 1
    else: edge_failed += 1

    # Edge Case 2: Event title requiring fuzzy matching (missing apostrophe & hyphen vs en-dash)
    e2_res = graphrag__lookup(ctx, "Sailing at the 2016 Summer Olympics - Womens RS:X")
    e2_pass = e2_res.get("ok") and e2_res.get("summary") == "26"
    print(f"[{'PASS' if e2_pass else 'FAIL'}] Edge 2 (Fuzzy Title Match): ok={e2_res.get('ok')} | Nations: {e2_res.get('summary')}")
    if e2_pass: edge_passed += 1
    else: edge_failed += 1

    # Edge Case 3: Aggregation with no matching sport/games
    e3_res = graphrag__aggregate(ctx, "Underwater Polo", "1800 Summer Olympics", 10)
    e3_pass = not e3_res.get("ok")
    print(f"[{'PASS' if e3_pass else 'FAIL'}] Edge 3 (Agg Nonexistent Sport): ok={e3_res.get('ok')} | Summary: {e3_res.get('summary')}")
    if e3_pass: edge_passed += 1
    else: edge_failed += 1

    # Edge Case 4: Superlative with no matching sport/games
    e4_res = graphrag__superlative(ctx, "Underwater Polo", "1800 Summer Olympics")
    e4_pass = not e4_res.get("ok")
    print(f"[{'PASS' if e4_pass else 'FAIL'}] Edge 4 (Sup Nonexistent Sport): ok={e4_res.get('ok')} | Summary: {e4_res.get('summary')}")
    if e4_pass: edge_passed += 1
    else: edge_failed += 1

    # Edge Case 5: Temporal event with prev_year present in graph
    e5_res = graphrag__temporal_resolve(ctx, "men's 20 kilometres walk", "Summer", 2016)
    e5_pass = e5_res.get("ok") and e5_res.get("context", {}).get("used_prev_graph") is True and e5_res.get("summary") == "Chen Ding"
    print(f"[{'PASS' if e5_pass else 'FAIL'}] Edge 5 (Temporal Graph Link Present): ok={e5_res.get('ok')} | UsedPrevGraph: {e5_res.get('context', {}).get('used_prev_graph')} | Gold: {e5_res.get('summary')}")
    if e5_pass: edge_passed += 1
    else: edge_failed += 1

    # Edge Case 6: Temporal event where prev_year is missing (inauguration event 2008 Marathon swimming)
    e6_res = graphrag__temporal_resolve(ctx, "Women's 10 kilometre marathon swimming", "Summer", 2008)
    e6_pass = not e6_res.get("ok")
    print(f"[{'PASS' if e6_pass else 'FAIL'}] Edge 6 (Temporal Prev Missing Clean Failure): ok={e6_res.get('ok')} | Summary: {e6_res.get('summary')}")
    if e6_pass: edge_passed += 1
    else: edge_failed += 1

    # --------------------------------------------------------------------------
    # SUMMARY GATE REPORT
    # --------------------------------------------------------------------------
    print("\n==========================================================================")
    print("                    PHASE 6 SUMMARY GATE REPORT                           ")
    print("==========================================================================")
    print(f"Tool 1 (graphrag__lookup):            {'PASS' if lookup_failed == 0 else 'FAIL'} | Passed: {lookup_passed} | Failed: {lookup_failed} | Total: {len(lookup_questions)}")
    print(f"Tool 2 (graphrag__aggregate):         {'PASS' if agg_failed == 0 else 'FAIL'} | Passed: {agg_passed} | Failed: {agg_failed} | Total: {len(agg_questions)}")
    print(f"Tool 3 (graphrag__superlative):       {'PASS' if sup_failed == 0 else 'FAIL'} | Passed: {sup_passed} | Failed: {sup_failed} | Total: {len(sup_questions)}")
    print(f"Tool 4 (graphrag__temporal_resolve):  {'PASS' if temp_failed == 0 else 'FAIL'} | Passed: {temp_passed} | Failed: {temp_failed} | Total: {len(temp_questions)}")
    print(f"Edge-Case Verification Suite:        {'PASS' if edge_failed == 0 else 'FAIL'} | Passed: {edge_passed} | Failed: {edge_failed} | Total: 6")

    total_tested = len(lookup_questions) + len(agg_questions) + len(sup_questions) + len(temp_questions) + 6
    total_passed = lookup_passed + agg_passed + sup_passed + temp_passed + edge_passed
    total_failed = lookup_failed + agg_failed + sup_failed + temp_failed + edge_failed

    print("--------------------------------------------------------------------------")
    print(f"TOTAL PHASE 6 SUITE RESULT: {'PASS' if total_failed == 0 else 'FAIL'} ({total_passed}/{total_tested} test cases passed)")
    print("==========================================================================")

    return {
        "lookup": {"pass": lookup_failed == 0, "passed": lookup_passed, "failed": lookup_failed, "total": len(lookup_questions), "failures": lookup_failures},
        "aggregate": {"pass": agg_failed == 0, "passed": agg_passed, "failed": agg_failed, "total": len(agg_questions), "failures": agg_failures},
        "superlative": {"pass": sup_failed == 0, "passed": sup_passed, "failed": sup_failed, "total": len(sup_questions), "failures": sup_failures},
        "temporal": {"pass": temp_failed == 0, "passed": temp_passed, "failed": temp_failed, "total": len(temp_questions), "failures": temp_failures},
        "edge_cases": {"pass": edge_failed == 0, "passed": edge_passed, "failed": edge_failed, "total": 6},
        "overall_pass": total_failed == 0
    }

if __name__ == "__main__":
    res = run_phase6_standalone_tests()
    if not res["overall_pass"]:
        sys.exit(1)
