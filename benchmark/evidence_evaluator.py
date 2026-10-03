"""
Evidence Evaluator for Agentic GraphRAG Benchmark (Phase 9.5).

Provides centralized, reproducible evidence telemetry extraction, normalization,
and multi-category gold hit evaluation (chunk/doc, vertex/entity, deterministic tool, citation)
without modifying any agentic pipeline components.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple, Set


def normalize_evidence_id(id_str: str) -> str:
    """Centralized normalization for evidence and document IDs:
    - Strips leading/trailing whitespace
    - Lowercases
    - Normalizes case-insensitive chunk notation (e.g. Q580481_CHUNK_0 -> q580481_chunk_0)
    """
    if not id_str or not isinstance(id_str, str):
        return ""
    return id_str.strip().lower()


def extract_doc_id_from_chunk_id(chunk_id: str) -> Optional[str]:
    """Extracts document ID (e.g. 'q580481') from chunk ID (e.g. 'q580481_chunk_0')."""
    if not chunk_id:
        return None
    m = re.match(r"^([a-zA-Z0-9_\-]+)_chunk_\d+$", chunk_id.strip(), re.IGNORECASE)
    if m:
        return m.group(1).lower()
    return None


def extract_evidence_from_payload(
    query_sources: Optional[Dict[str, Any]] = None,
    agent_steps: Optional[List[Dict[str, Any]]] = None,
    citations: Optional[List[str]] = None,
    olympic_doc_ids: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Extracts complete disaggregated evidence sets from agentic query response:
    1. Chunk / Doc evidence (text retrieval layer)
    2. Vertex / Entity evidence (graph exploration layer)
    3. Tool evidence (deterministic tool invocations)
    4. Citation evidence (synthesizer citations)
    5. Retrieval intrusion calculation (computed only on actual retrieved doc IDs)
    """
    retrieved_chunk_ids_raw: Set[str] = set()
    retrieved_vertex_ids_raw: Set[str] = set()
    cited_chunk_ids_raw: Set[str] = set()
    cited_vertex_ids_raw: Set[str] = set()
    
    deterministic_tools_used: List[str] = []
    deterministic_tool_evidence: Dict[str, Any] = {}
    
    # 1. Parse citations if available
    if citations and isinstance(citations, list):
        for cit in citations:
            if not isinstance(cit, str):
                continue
            cit_clean = cit.strip()
            if re.search(r"_chunk_\d+$", cit_clean, re.IGNORECASE):
                cited_chunk_ids_raw.add(cit_clean)
            elif re.match(r"^Q\d+$", cit_clean, re.IGNORECASE):
                cited_vertex_ids_raw.add(cit_clean)
            else:
                # e.g., 'structural', 'graphrag__lookup', etc.
                pass

    # Normalize agent_steps
    steps = agent_steps or []
    if not steps and isinstance(query_sources, dict):
        steps = query_sources.get("agent_steps", [])

    # 2. Extract from agent_steps
    for step in steps:
        if not isinstance(step, dict):
            continue
        
        node = step.get("node", "")
        tool = step.get("tool", "")
        output = step.get("output")
        inp = step.get("input")

        # Track deterministic tools
        if tool:
            if tool in ("graphrag__lookup", "graphrag__temporal_resolve", "graphrag__aggregate", "graphrag__superlative", "graphrag__structural_retrieve"):
                deterministic_tools_used.append(tool)
        elif node and "graphrag__" in node:
            tname = node.split(":")[-1].strip() if ":" in node else node
            deterministic_tools_used.append(tname)

        # Parse output
        if output is None:
            continue

        # If output is string (e.g. JSON string)
        if isinstance(output, str):
            # Check for chunk IDs in text
            for m in re.findall(r"([a-zA-Z0-9_\-]+_chunk_\d+)", output):
                retrieved_chunk_ids_raw.add(m)
            # Try parse JSON
            try:
                out_dict = json.loads(output)
                if isinstance(out_dict, dict):
                    output = out_dict
            except Exception:
                pass

        if isinstance(output, dict):
            # Context / Result extraction
            res = output.get("result")
            ctx = output.get("context", {})
            if isinstance(ctx, dict) and "result" in ctx:
                res = ctx.get("result")

            if isinstance(res, dict):
                # 2a. Check final_retrieval
                fin_ret = res.get("final_retrieval")
                if isinstance(fin_ret, dict):
                    for k in fin_ret.keys():
                        retrieved_chunk_ids_raw.add(str(k))

                # 2b. Check preview string for serialized final_retrieval
                preview = res.get("preview")
                if isinstance(preview, str):
                    for m in re.findall(r"([a-zA-Z0-9_\-]+_chunk_\d+)", preview):
                        retrieved_chunk_ids_raw.add(m)

                # 2c. Check event_id or id (graph vertex)
                eid = res.get("event_id")
                if eid:
                    retrieved_vertex_ids_raw.add(str(eid))
                    deterministic_tool_evidence["event_id"] = str(eid)

                vid = res.get("id")
                if vid:
                    retrieved_vertex_ids_raw.add(str(vid))

                # 2d. Check result list (e.g., lookup / superlative / temporal rows)
                res_list = res.get("result")
                if isinstance(res_list, list):
                    for row in res_list:
                        if isinstance(row, dict):
                            if "event_id" in row and row["event_id"]:
                                retrieved_vertex_ids_raw.add(str(row["event_id"]))
                            if "id" in row and row["id"]:
                                retrieved_vertex_ids_raw.add(str(row["id"]))
                            if "winner_id" in row and row["winner_id"]:
                                retrieved_vertex_ids_raw.add(str(row["winner_id"]))
                            if "edition_id" in row and row["edition_id"]:
                                retrieved_vertex_ids_raw.add(str(row["edition_id"]))

                # 2e. Check aggregation / scalar tool results
                if "total_events" in res or "count" in res or "aggregation" in res:
                    deterministic_tool_evidence.update(res)

            elif isinstance(res, list):
                for row in res:
                    if isinstance(row, dict):
                        if "event_id" in row and row["event_id"]:
                            retrieved_vertex_ids_raw.add(str(row["event_id"]))
                        if "id" in row and row["id"]:
                            retrieved_vertex_ids_raw.add(str(row["id"]))

    # 3. If query_sources was passed, check top-level query_sources string fallback
    if query_sources and isinstance(query_sources, dict):
        qs_str = json.dumps(query_sources)
        for m in re.findall(r"([a-zA-Z0-9_\-]+_chunk_\d+)", qs_str):
            retrieved_chunk_ids_raw.add(m)

    # 4. Compute derived Doc IDs
    retrieved_chunk_ids = sorted(list(retrieved_chunk_ids_raw))
    retrieved_doc_ids_set = set()
    for c in retrieved_chunk_ids:
        doc_id = extract_doc_id_from_chunk_id(c)
        if doc_id:
            retrieved_doc_ids_set.add(doc_id.upper())
    retrieved_doc_ids = sorted(list(retrieved_doc_ids_set))

    retrieved_vertex_ids = sorted(list(retrieved_vertex_ids_raw))

    cited_chunk_ids = sorted(list(cited_chunk_ids_raw))
    cited_doc_ids_set = set()
    for c in cited_chunk_ids:
        doc_id = extract_doc_id_from_chunk_id(c)
        if doc_id:
            cited_doc_ids_set.add(doc_id.upper())
    cited_doc_ids = sorted(list(cited_doc_ids_set))
    cited_vertex_ids = sorted(list(cited_vertex_ids_raw))

    # 5. Compute Retrieval Intrusion at K (Text chunk retrieval only)
    intrusion_pct = None
    if retrieved_doc_ids and olympic_doc_ids:
        olympic_upper = {d.upper() for d in olympic_doc_ids}
        non_olympic_count = sum(1 for d in retrieved_doc_ids if d.upper() not in olympic_upper)
        intrusion_pct = round((non_olympic_count / len(retrieved_doc_ids)) * 100, 2)

    return {
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "retrieved_doc_ids": retrieved_doc_ids,
        "retrieved_vertex_ids": retrieved_vertex_ids,
        "cited_chunk_ids": cited_chunk_ids,
        "cited_doc_ids": cited_doc_ids,
        "cited_vertex_ids": cited_vertex_ids,
        "deterministic_tools_used": deterministic_tools_used,
        "deterministic_tool_evidence": deterministic_tool_evidence,
        "retrieval_intrusion_at_k": intrusion_pct,
    }


def evaluate_gold_evidence(
    evidence: Dict[str, Any],
    gold_doc_ids: List[str],
    qtype: str,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates evidence against gold document IDs across disaggregated categories:
    - gold_chunk_hit: bool or None (None for deterministic pure-graph tools where chunks are N/A)
    - gold_vertex_hit: bool or None
    - gold_tool_evidence_hit: bool or None
    - cited_gold_hit: bool or None
    - gold_hit_combined: bool (True if authoritative gold evidence was in chunk, vertex, or tool)
    """
    if error:
        return {
            "gold_chunk_hit": False if qtype == "multi_hop" else (None if qtype == "aggregation" else False),
            "gold_vertex_hit": None if qtype == "aggregation" else False,
            "gold_tool_evidence_hit": None if qtype == "multi_hop" else False,
            "cited_gold_hit": False,
            "gold_hit_combined": False,
            "is_evaluable": False,
        }

    norm_gold_ids = [normalize_evidence_id(g) for g in (gold_doc_ids or []) if g]
    gold_set = set(norm_gold_ids)

    norm_ret_docs = {normalize_evidence_id(d) for d in evidence.get("retrieved_doc_ids", [])}
    norm_ret_vertices = {normalize_evidence_id(v) for v in evidence.get("retrieved_vertex_ids", [])}
    norm_cited_docs = {normalize_evidence_id(d) for d in evidence.get("cited_doc_ids", [])}
    norm_cited_vertices = {normalize_evidence_id(v) for v in evidence.get("cited_vertex_ids", [])}

    # 1. Chunk Hit
    gold_chunk_hit: Optional[bool] = None
    if norm_ret_docs:
        gold_chunk_hit = bool(norm_ret_docs.intersection(gold_set))
    elif qtype in ("multi_hop", "lookup"):
        # Multi-hop and lookup expect retrieval if not purely structural
        gold_chunk_hit = False if not norm_ret_vertices else None

    # 2. Vertex Hit
    gold_vertex_hit: Optional[bool] = None
    if norm_ret_vertices:
        gold_vertex_hit = bool(norm_ret_vertices.intersection(gold_set))
    elif qtype in ("temporal", "superlative", "lookup"):
        gold_vertex_hit = False

    # 3. Deterministic Tool Evidence Hit
    gold_tool_evidence_hit: Optional[bool] = None
    tools_used = evidence.get("deterministic_tools_used", [])
    if any(t in ("graphrag__aggregate", "graphrag__lookup", "graphrag__temporal_resolve", "graphrag__superlative", "graphrag__structural_retrieve") for t in tools_used):
        # If aggregation, tool ran directly on TigerGraph
        if qtype == "aggregation":
            gold_tool_evidence_hit = True
            gold_chunk_hit = None
            gold_vertex_hit = None
        else:
            gold_tool_evidence_hit = bool((norm_ret_vertices.union(norm_ret_docs)).intersection(gold_set))
    elif qtype == "aggregation":
        gold_tool_evidence_hit = True
        gold_chunk_hit = None
        gold_vertex_hit = None

    # 4. Cited Gold Hit
    cited_all = norm_cited_docs.union(norm_cited_vertices)
    cited_gold_hit = bool(cited_all.intersection(gold_set)) if cited_all and gold_set else False

    # 5. Combined Gold Hit
    # Authoritative gold evidence surfaced anywhere to agent (chunk, vertex, or deterministic tool)
    if qtype == "aggregation":
        gold_hit_combined = True if gold_tool_evidence_hit else False
    else:
        all_retrieved = norm_ret_docs.union(norm_ret_vertices)
        gold_hit_combined = bool(all_retrieved.intersection(gold_set)) if gold_set else False

    return {
        "gold_chunk_hit": gold_chunk_hit,
        "gold_vertex_hit": gold_vertex_hit,
        "gold_tool_evidence_hit": gold_tool_evidence_hit,
        "cited_gold_hit": cited_gold_hit,
        "gold_hit_combined": gold_hit_combined,
        "is_evaluable": True,
    }
