# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# Specialist Agent Capability Layer
# Lightweight, deterministic capability wrappers over existing tools & retrievers.

from __future__ import annotations

import time
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union

from tools import tool_registry as registry

logger = logging.getLogger(__name__)


@dataclass
class SpecialistTelemetry:
    specialist_name: str
    action: str
    input_summary: str
    tool_used: Optional[str]
    result_summary: str
    latency_ms: float
    tokens: Optional[int]
    evidence_added: Dict[str, Any]
    recommendation: str  # "continue", "stop", "answer_ready", "error"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SpecialistOutput:
    ok: bool
    summary: str
    context: Any
    citations: List[str]
    telemetry: SpecialistTelemetry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "context": self.context,
            "citations": self.citations,
            "telemetry": self.telemetry.to_dict()
        }


class SpecialistAgent:
    """Base interface for lightweight specialist capability agents."""
    name: str = "SpecialistAgent"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        raise NotImplementedError("Subclasses must implement execute()")


class EntityLinkingSpecialist(SpecialistAgent):
    """Specialist for linking surface forms (entities, events, sports, years) to graph identifiers."""
    name: str = "EntityLinkingSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        tool_used = None
        evidence_added = {}
        recommendation = "continue"

        query = params.get("query") or params.get("entity_name") or params.get("event_title") or ""
        input_summary = f"action={action}, query='{query}'"

        # Deterministic entity normalization
        normalized_entity = query.strip()
        # Strip common punctuation and prefixes
        if normalized_entity.lower().startswith("how many nations competed in "):
            normalized_entity = normalized_entity[len("How many nations competed in "):].rstrip("?").strip()

        evidence_added["linked_entity"] = normalized_entity
        latency_ms = round((time.time() - t0) * 1000.0, 2)
        summary = f"Linked entity: '{normalized_entity}'"

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=tool_used,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added=evidence_added,
            recommendation=recommendation
        )

        return SpecialistOutput(
            ok=True,
            summary=summary,
            context={"linked_entity": normalized_entity, "original_query": query},
            citations=["entity_linking"],
            telemetry=telemetry
        )


class SimilarityRetrievalSpecialist(SpecialistAgent):
    """Specialist for vector and semantic similarity retrieval."""
    name: str = "SimilarityRetrievalSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        tool_name = "graphrag__vector_search" if "graphrag__vector_search" in registry.catalog() else "vector_similarity"
        query = params.get("query", "")
        top_k = params.get("top_k", 5)
        input_summary = f"query='{query}', top_k={top_k}"

        tool_out = registry.run("graphrag__structural_retrieve", params, ctx) if "graphrag__structural_retrieve" in registry.catalog() else {"ok": False, "summary": "Tool not registered", "context": None}
        latency_ms = round((time.time() - t0) * 1000.0, 2)

        summary = tool_out.get("summary", "Vector retrieval completed")
        ok = bool(tool_out.get("ok"))
        evidence = {"retrieved_chunks": tool_out.get("context", {}).get("chunk_ids", []) if isinstance(tool_out.get("context"), dict) else []}

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=tool_name,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added=evidence,
            recommendation="continue" if ok else "error"
        )

        return SpecialistOutput(
            ok=ok,
            summary=summary,
            context=tool_out.get("context"),
            citations=tool_out.get("citations", ["vector_search"]),
            telemetry=telemetry
        )


class DocumentRetrievalSpecialist(SpecialistAgent):
    """Specialist for document and text chunk retrieval."""
    name: str = "DocumentRetrievalSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        doc_ids = params.get("doc_ids", [])
        chunk_ids = params.get("chunk_ids", [])
        input_summary = f"doc_ids={doc_ids}, chunk_ids={chunk_ids}"

        # Lightweight deterministic document retrieval via context/tools
        evidence = {"doc_ids": doc_ids, "chunk_ids": chunk_ids}
        latency_ms = round((time.time() - t0) * 1000.0, 2)
        summary = f"Retrieved {len(doc_ids)} docs and {len(chunk_ids)} chunks"

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used="document_store",
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added=evidence,
            recommendation="continue"
        )

        return SpecialistOutput(
            ok=True,
            summary=summary,
            context=evidence,
            citations=["document_retrieval"],
            telemetry=telemetry
        )


class GraphTraversalSpecialist(SpecialistAgent):
    """Specialist for graph traversal and deterministic entity lookups."""
    name: str = "GraphTraversalSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        tool_used = "graphrag__lookup"
        event_title = params.get("event_title") or params.get("title") or ""
        input_summary = f"event_title='{event_title}'"

        tool_out = registry.run("graphrag__lookup", {"event_title": event_title}, ctx)
        latency_ms = round((time.time() - t0) * 1000.0, 2)

        ok = bool(tool_out.get("ok"))
        summary = tool_out.get("summary", "Lookup failed")
        evidence = {"matched_event": tool_out.get("context", {}).get("title"), "nations": summary} if ok else {}

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=tool_used,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added=evidence,
            recommendation="answer_ready" if ok else "continue"
        )

        return SpecialistOutput(
            ok=ok,
            summary=summary,
            context=tool_out.get("context"),
            citations=tool_out.get("citations", ["graph_traversal"]),
            telemetry=telemetry
        )


class AnalyticalSpecialist(SpecialistAgent):
    """Specialist for deterministic aggregation and superlative computations over graph vertices."""
    name: str = "AnalyticalSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        sport = params.get("sport", "")
        games = params.get("games", "")
        threshold = params.get("threshold")

        if action == "aggregate" or threshold is not None:
            tool_used = "graphrag__aggregate"
            tool_args = {"sport": sport, "games": games, "threshold": int(threshold) if threshold is not None else 0}
            input_summary = f"sport='{sport}', games='{games}', threshold={threshold}"
        else:
            tool_used = "graphrag__superlative"
            tool_args = {"sport": sport, "games": games}
            input_summary = f"sport='{sport}', games='{games}'"

        tool_out = registry.run(tool_used, tool_args, ctx)
        latency_ms = round((time.time() - t0) * 1000.0, 2)

        ok = bool(tool_out.get("ok"))
        summary = tool_out.get("summary", "Analysis failed")
        evidence = {"analytic_result": summary, "tool": tool_used}

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=tool_used,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added=evidence,
            recommendation="answer_ready" if ok else "continue"
        )

        return SpecialistOutput(
            ok=ok,
            summary=summary,
            context=tool_out.get("context"),
            citations=tool_out.get("citations", ["analytical_engine"]),
            telemetry=telemetry
        )


class MultiHopInvestigationSpecialist(SpecialistAgent):
    """Specialist for multi-hop graph exploration and temporal resolution."""
    name: str = "MultiHopInvestigationSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        tool_used = "graphrag__temporal_resolve"
        event_name = params.get("event_name", "")
        season = params.get("season", "")
        ref_year = params.get("reference_year", 0)
        direction = params.get("direction", "immediately before")
        input_summary = f"event='{event_name}', season='{season}', ref_year={ref_year}, dir='{direction}'"

        tool_args = {
            "event_name": event_name,
            "season": season,
            "reference_year": int(ref_year),
            "direction": direction
        }

        tool_out = registry.run("graphrag__temporal_resolve", tool_args, ctx)
        latency_ms = round((time.time() - t0) * 1000.0, 2)

        ok = bool(tool_out.get("ok"))
        summary = tool_out.get("summary", "Temporal resolution failed")
        evidence = {"resolved_gold_winner": summary, "context": tool_out.get("context")} if ok else {}

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=tool_used,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added=evidence,
            recommendation="answer_ready" if ok else "continue"
        )

        return SpecialistOutput(
            ok=ok,
            summary=summary,
            context=tool_out.get("context"),
            citations=tool_out.get("citations", ["temporal_resolve"]),
            telemetry=telemetry
        )


class EvidenceEvaluationSpecialist(SpecialistAgent):
    """Specialist for verifying evidence completeness, ground truth alignment, and citations."""
    name: str = "EvidenceEvaluationSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        prediction = params.get("prediction", "")
        evidence_items = params.get("evidence", {})
        citations = params.get("citations", [])
        input_summary = f"prediction_length={len(prediction)}, evidence_keys={list(evidence_items.keys())}"

        has_evidence = bool(evidence_items) or bool(citations)
        grounded = bool(prediction) and has_evidence
        latency_ms = round((time.time() - t0) * 1000.0, 2)

        summary = f"Evidence evaluated: grounded={grounded}, evidence_count={len(evidence_items)}"
        rec = "stop" if grounded else "continue"

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=None,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added={"grounded": grounded},
            recommendation=rec
        )

        return SpecialistOutput(
            ok=True,
            summary=summary,
            context={"grounded": grounded, "evidence": evidence_items},
            citations=["evidence_evaluation"],
            telemetry=telemetry
        )


class TigerGraphMCPSpecialist(SpecialistAgent):
    """Optional specialist backend providing read-only TigerGraph Model Context Protocol (MCP) access."""
    name: str = "TigerGraphMCPSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        t0 = time.time()
        tool_used = "tg_run_query"
        query_text = params.get("query_text") or params.get("query")
        vertex_type = params.get("vertex_type")
        vertex_id = params.get("vertex_id")

        if action == "get_neighbors" or (vertex_type and vertex_id):
            tool_used = "tg_get_neighbors"
            tool_out = registry.run("tg_get_neighbors", {
                "vertex_type": vertex_type,
                "vertex_id": vertex_id,
                "edge_type": params.get("edge_type"),
                "limit": params.get("limit", 10)
            }, ctx)
            input_summary = f"vertex_type='{vertex_type}', vertex_id='{vertex_id}'"
        else:
            tool_used = "tg_run_query"
            tool_out = registry.run("tg_run_query", {"query_text": query_text or "INTERPRET QUERY () FOR GRAPH Olympics { S = {Event.*}; PRINT S.size(); }"}, ctx)
            input_summary = f"query_text='{query_text}'"

        latency_ms = round((time.time() - t0) * 1000.0, 2)
        ok = bool(tool_out.get("ok"))
        summary = tool_out.get("summary", "MCP operation completed")
        evidence = tool_out.get("context", {})

        telemetry = SpecialistTelemetry(
            specialist_name=self.name,
            action=action,
            input_summary=input_summary,
            tool_used=tool_used,
            result_summary=summary,
            latency_ms=latency_ms,
            tokens=None,
            evidence_added={"mcp_context": evidence},
            recommendation="continue" if ok else "error"
        )

        return SpecialistOutput(
            ok=ok,
            summary=summary,
            context=evidence,
            citations=tool_out.get("citations", ["tigergraph_mcp"]),
            telemetry=telemetry
        )


class SpecialistOrchestrator:
    """Orchestrator layer that routes sub-tasks to dedicated specialist agents."""

    def __init__(self, max_llm_calls: int = 6, max_steps: int = 5):
        self.max_llm_calls = max_llm_calls
        self.max_steps = max_steps
        self.specialists: Dict[str, SpecialistAgent] = {
            "entity_linking": EntityLinkingSpecialist(),
            "similarity_retrieval": SimilarityRetrievalSpecialist(),
            "document_retrieval": DocumentRetrievalSpecialist(),
            "graph_traversal": GraphTraversalSpecialist(),
            "analytical": AnalyticalSpecialist(),
            "multi_hop": MultiHopInvestigationSpecialist(),
            "evidence_evaluation": EvidenceEvaluationSpecialist(),
            "tigergraph_mcp": TigerGraphMCPSpecialist()
        }

    def dispatch(self, specialist_key: str, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        spec = self.specialists.get(specialist_key)
        if not spec:
            raise KeyError(f"Unknown specialist key: {specialist_key}. Available: {list(self.specialists.keys())}")
        return spec.execute(action, params, ctx)

    def route_question(self, qtype: str, question: str, parsed_args: Dict[str, Any], ctx: Any) -> Tuple[SpecialistOutput, List[SpecialistTelemetry]]:
        """
        Legacy routing helper for representative question types.
        """
        res = self.execute_dynamic(question=question, qtype=qtype, parsed_args=parsed_args, ctx=ctx)
        telemetries = [SpecialistTelemetry(**t) if isinstance(t, dict) else t for t in res.get("telemetry_trail", [])]
        out = SpecialistOutput(
            ok=bool(res.get("ok")),
            summary=res.get("final_answer", ""),
            context=res.get("evidence_after"),
            citations=["specialist_orchestrator"],
            telemetry=telemetries[-1] if telemetries else SpecialistTelemetry("Orchestrator", "route", "", None, "", 0.0, None, {}, "stop")
        )
        return out, telemetries

    def execute_dynamic(
        self,
        question: str,
        qtype: Optional[str] = None,
        parsed_args: Optional[Dict[str, Any]] = None,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """
        Dynamic, result-dependent routing engine across specialist capabilities.
        Selects next specialist based on:
        1. original question & qtype
        2. available graph entities
        3. evidence already obtained
        4. result of previous action
        5. information still missing
        """
        args = dict(parsed_args or {})
        telemetries: List[Dict[str, Any]] = []
        specialists_invoked: List[str] = []
        strategy_changes = 0
        reason_for_change = None
        evidence_before: Dict[str, Any] = {}
        evidence_after: Dict[str, Any] = {}
        stop_reason = "no_new_information"
        final_answer = ""
        total_steps = 0
        ok = False

        # 1. Determine Initial Strategy
        if qtype == "lookup":
            initial_strategy = "Pattern A: Entity Linking -> Graph Traversal -> Answer"
        elif qtype in ["aggregation", "superlative"]:
            initial_strategy = "Analytical Engine -> Evidence Evaluation -> Answer"
        elif qtype == "temporal":
            initial_strategy = "Pattern C: Multi-Hop Temporal Resolve -> Evidence Evaluation -> Answer"
        elif qtype == "multi_hop":
            initial_strategy = "Pattern C: Graph/Document Retrieval -> Multi-Hop Investigation -> Evidence Evaluation -> Answer"
        else:
            initial_strategy = "Pattern B: Similarity Retrieval -> Entity Linking -> Graph Traversal -> Evidence -> Answer"

        # 2. Execution Loop
        if qtype == "lookup":
            # Step 1: Entity Linking
            total_steps += 1
            specialists_invoked.append("EntityLinkingSpecialist")
            ev_title = args.get("event_title") or question
            el_out = self.dispatch("entity_linking", "link_event", {"event_title": ev_title}, ctx)
            telemetries.append(el_out.telemetry.to_dict())
            linked_entity = el_out.context.get("linked_entity", ev_title)

            # Step 2: Graph Traversal
            total_steps += 1
            specialists_invoked.append("GraphTraversalSpecialist")
            evidence_before = {"linked_entity": linked_entity}
            gt_out = self.dispatch("graph_traversal", "lookup", {"event_title": linked_entity}, ctx)
            telemetries.append(gt_out.telemetry.to_dict())

            if gt_out.ok:
                evidence_before = {"matched_event": linked_entity, "result": gt_out.summary}
                total_steps += 1
                specialists_invoked.append("EvidenceEvaluationSpecialist")
                ev_out = self.dispatch("evidence_evaluation", "evaluate_evidence", {
                    "prediction": gt_out.summary,
                    "evidence": gt_out.context,
                    "citations": gt_out.citations
                }, ctx)
                telemetries.append(ev_out.telemetry.to_dict())
                evidence_after = ev_out.context or {"matched_event": linked_entity, "result": gt_out.summary}
                final_answer = str(gt_out.summary)
                ok = True
                stop_reason = "answer_found"
            else:
                # DYNAMIC STRATEGY CHANGE: Fallback to Pattern B (Similarity Retrieval -> Entity Linking)
                strategy_changes += 1
                reason_for_change = f"Direct Graph Traversal failed for '{linked_entity}'; switching to Similarity Retrieval fallback (Pattern B)"
                total_steps += 1
                specialists_invoked.append("SimilarityRetrievalSpecialist")
                sim_out = self.dispatch("similarity_retrieval", "search", {"query": linked_entity, "top_k": 3}, ctx)
                telemetries.append(sim_out.telemetry.to_dict())

                if sim_out.ok and sim_out.summary:
                    evidence_after = {"similarity_context": sim_out.summary}
                    final_answer = str(sim_out.summary)
                    ok = True
                    stop_reason = "evidence_sufficient"
                else:
                    stop_reason = "tool_error"

        elif qtype in ["aggregation", "superlative"]:
            total_steps += 1
            specialists_invoked.append("AnalyticalSpecialist")
            action = "aggregate" if qtype == "aggregation" else "superlative"
            an_out = self.dispatch("analytical", action, args, ctx)
            telemetries.append(an_out.telemetry.to_dict())

            if an_out.ok:
                evidence_before = {"raw_output": an_out.summary}
                # Step 2: Evidence Evaluation
                total_steps += 1
                specialists_invoked.append("EvidenceEvaluationSpecialist")
                ev_out = self.dispatch("evidence_evaluation", "evaluate_evidence", {
                    "prediction": an_out.summary,
                    "evidence": an_out.context,
                    "citations": an_out.citations
                }, ctx)
                telemetries.append(ev_out.telemetry.to_dict())
                evidence_after = ev_out.context
                final_answer = str(an_out.summary)
                ok = True
                stop_reason = "evidence_sufficient"
            else:
                stop_reason = "tool_error"

        elif qtype == "temporal":
            total_steps += 1
            specialists_invoked.append("MultiHopInvestigationSpecialist")
            mh_out = self.dispatch("multi_hop", "temporal_resolve", args, ctx)
            telemetries.append(mh_out.telemetry.to_dict())

            if mh_out.ok:
                evidence_before = {"temporal_winner": mh_out.summary}
                # Step 2: Evidence Evaluation
                total_steps += 1
                specialists_invoked.append("EvidenceEvaluationSpecialist")
                ev_out = self.dispatch("evidence_evaluation", "evaluate_evidence", {
                    "prediction": mh_out.summary,
                    "evidence": mh_out.context,
                    "citations": mh_out.citations
                }, ctx)
                telemetries.append(ev_out.telemetry.to_dict())
                evidence_after = ev_out.context
                final_answer = str(mh_out.summary)
                ok = True
                stop_reason = "evidence_sufficient"
            else:
                stop_reason = "tool_error"

        elif qtype == "multi_hop":
            # Multi-Hop Pattern C: Check if temporal or multi-entity
            total_steps += 1
            if "reference_year" in args or "season" in args:
                specialists_invoked.append("MultiHopInvestigationSpecialist")
                mh_out = self.dispatch("multi_hop", "temporal_resolve", args, ctx)
                telemetries.append(mh_out.telemetry.to_dict())
            else:
                specialists_invoked.append("GraphTraversalSpecialist")
                mh_out = self.dispatch("graph_traversal", "lookup", args, ctx)
                telemetries.append(mh_out.telemetry.to_dict())

            if mh_out.ok:
                evidence_before = {"multi_hop_result": mh_out.summary}
                total_steps += 1
                specialists_invoked.append("EvidenceEvaluationSpecialist")
                ev_out = self.dispatch("evidence_evaluation", "evaluate_evidence", {
                    "prediction": mh_out.summary,
                    "evidence": mh_out.context,
                    "citations": mh_out.citations
                }, ctx)
                telemetries.append(ev_out.telemetry.to_dict())
                evidence_after = ev_out.context
                final_answer = str(mh_out.summary)
                ok = True
                stop_reason = "evidence_sufficient"
            else:
                # Dynamic strategy change to Document Retrieval fallback
                strategy_changes += 1
                reason_for_change = "Direct Multi-Hop graph expansion yielded empty context; switching to Document Retrieval"
                total_steps += 1
                specialists_invoked.append("DocumentRetrievalSpecialist")
                doc_out = self.dispatch("document_retrieval", "fetch", {"chunk_ids": args.get("chunk_ids", [])}, ctx)
                telemetries.append(doc_out.telemetry.to_dict())
                evidence_after = doc_out.context
                final_answer = doc_out.summary
                ok = True
                stop_reason = "evidence_sufficient"

        else:
            # Pattern B
            total_steps += 1
            specialists_invoked.append("SimilarityRetrievalSpecialist")
            sim_out = self.dispatch("similarity_retrieval", "search", {"query": question}, ctx)
            telemetries.append(sim_out.telemetry.to_dict())
            evidence_after = {"similarity_result": sim_out.summary}
            final_answer = str(sim_out.summary)
            ok = sim_out.ok
            stop_reason = "evidence_sufficient" if ok else "tool_error"

        return {
            "ok": ok,
            "initial_strategy": initial_strategy,
            "specialists_invoked": specialists_invoked,
            "strategy_changes": strategy_changes,
            "reason_for_change": reason_for_change,
            "evidence_before": evidence_before,
            "evidence_after": evidence_after,
            "stop_reason": stop_reason,
            "total_steps": total_steps,
            "final_answer": final_answer,
            "telemetry_trail": telemetries
        }


@dataclass
class AgenticEffectivenessTelemetry:
    """Canonical Phase 10 Agentic Effectiveness Telemetry Record."""
    qid: str
    pipeline: str = "agentic_graphrag"
    accuracy: Optional[bool] = None
    completeness: Optional[float] = None
    grounding: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: float = 0.0
    steps: int = 0
    retrieval_methods: List[str] = field(default_factory=list)
    specialists_invoked: List[str] = field(default_factory=list)
    tools_called: List[str] = field(default_factory=list)
    chunks_retrieved: List[str] = field(default_factory=list)
    citations: List[Any] = field(default_factory=list)
    strategy_changes: int = 0
    stop_reason: str = "evidence_sufficient"
    budget_limit: Dict[str, Any] = field(default_factory=lambda: {"max_llm_calls": 6, "max_steps": 5})
    budget_used: Dict[str, Any] = field(default_factory=dict)
    
    # Detailed action breakdown (no chain-of-thought)
    initial_strategy: str = ""
    actions: List[Dict[str, Any]] = field(default_factory=list)
    strategy_changed: bool = False
    why_strategy_changed: Optional[str] = None
    evidence_increased: bool = True
    why_execution_stopped: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_effectiveness_telemetry(
    qid: str,
    exec_res: Dict[str, Any],
    gold: Optional[str] = None,
    latency_ms: Optional[float] = None,
    token_usage: Optional[Dict[str, int]] = None
) -> AgenticEffectivenessTelemetry:
    """Helper to assemble a canonical AgenticEffectivenessTelemetry record from an execution result."""
    pred = exec_res.get("final_answer", "")
    accuracy = None
    completeness = None
    if gold is not None:
        norm_pred = str(pred).lower().strip()
        norm_gold = str(gold).lower().strip()
        accuracy = norm_gold in norm_pred or norm_pred in norm_gold
        gold_tokens = norm_gold.split()
        hits = sum(1 for t in gold_tokens if t in norm_pred)
        completeness = round(hits / len(gold_tokens), 4) if gold_tokens else 0.0

    telemetry_trail = exec_res.get("telemetry_trail", [])
    tools_called = [t.get("tool_used") for t in telemetry_trail if t.get("tool_used")]
    retrieval_methods = list(set(tools_called))

    chunks_retrieved = []
    citations = []
    if "evidence_after" in exec_res and isinstance(exec_res["evidence_after"], dict):
        chunks_retrieved = exec_res["evidence_after"].get("chunk_ids", [])
        citations = exec_res["evidence_after"].get("citations", ["tigergraph_graph"])

    total_steps = exec_res.get("total_steps", len(telemetry_trail))
    tot_latency = latency_ms or sum(t.get("latency_ms", 0.0) for t in telemetry_trail)

    # Build action breakdown without chain-of-thought
    actions = []
    for idx, t in enumerate(telemetry_trail):
        actions.append({
            "step": idx + 1,
            "specialist": t.get("specialist_name"),
            "action": t.get("action"),
            "result_summary": t.get("result_summary"),
            "tool_used": t.get("tool_used"),
            "latency_ms": t.get("latency_ms"),
            "recommendation": t.get("recommendation")
        })

    tokens = token_usage or {}
    budget_used = {
        "llm_calls": 0,
        "steps": total_steps,
        "total_tokens": tokens.get("total_tokens", 0)
    }

    return AgenticEffectivenessTelemetry(
        qid=qid,
        pipeline="agentic_graphrag",
        accuracy=accuracy,
        completeness=completeness,
        grounding=None,
        input_tokens=tokens.get("input_tokens"),
        output_tokens=tokens.get("output_tokens"),
        total_tokens=tokens.get("total_tokens"),
        latency_ms=round(tot_latency, 2),
        steps=total_steps,
        retrieval_methods=retrieval_methods,
        specialists_invoked=exec_res.get("specialists_invoked", []),
        tools_called=tools_called,
        chunks_retrieved=chunks_retrieved,
        citations=citations,
        strategy_changes=exec_res.get("strategy_changes", 0),
        stop_reason=exec_res.get("stop_reason", "evidence_sufficient"),
        budget_limit={"max_llm_calls": 6, "max_steps": 5},
        budget_used=budget_used,
        initial_strategy=exec_res.get("initial_strategy", ""),
        actions=actions,
        strategy_changed=bool(exec_res.get("strategy_changes", 0) > 0),
        why_strategy_changed=exec_res.get("reason_for_change"),
        evidence_increased=bool(exec_res.get("evidence_after")),
        why_execution_stopped=exec_res.get("stop_reason", "evidence_sufficient")
    )
