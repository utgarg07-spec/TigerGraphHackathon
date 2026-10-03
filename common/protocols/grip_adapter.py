# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# This program may be redistributed and/or modified under the terms of the GNU
# Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

"""GRIP v0.5.0 Standalone Canonical Adapter.

This module provides a pure-Python, deterministic transformation layer that converts
internal GraphRAGResponse, StepResult, and citation evidence into the GraphRAG
Interoperability Protocol (GRIP v0.5.0) Canonical Subgraph and Provenance envelope.

Design Guarantees:
- Downstream / read-only transformation: does NOT sit between planner and executor.
- Zero network, LLM, or TigerGraph calls.
- Pure SHA-256 cryptographic provenance hashing over exact, unmodified raw text chunks.
- Faithful schema extraction: unavailable fields are represented explicitly as empty
  or None rather than hallucinated/fabricated.
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from common.py_schemas import GraphRAGResponse, StepResult

logger = logging.getLogger(__name__)

GRIP_SPEC_VERSION = "0.5.0"


class GRIPModality(str, enum.Enum):
    """Canonical GRIP v0.5.0 Retrieval Modalities."""
    GLOBAL_COMMUNITY = "global_community_summary"
    LOCAL_ENTITY = "local_entity_subgraph"
    VECTOR_GRAPH_HYBRID = "vector_graph_hybrid"
    MULTI_HOP_PATH = "multi_hop_path"
    TEMPORAL_CAUSAL = "temporal_causal_subgraph"
    SCHEMA_CYPHER_GSQL = "schema_cypher_gsql"
    AUTO_ROUTED = "auto_routed"
    # Custom/extension modality for deterministic analytical operations
    DETERMINISTIC_ANALYTIC = "custom_deterministic_analytic"


class GRIPEntity(BaseModel):
    """Typed Entity representation in GRIP Subgraph."""
    id: str
    type: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GRIPRelationship(BaseModel):
    """Typed Directed Relationship representation in GRIP Subgraph."""
    source_id: str
    target_id: str
    type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GRIPPath(BaseModel):
    """Path traversal sequence in GRIP Subgraph."""
    path_id: Optional[str] = None
    nodes: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)


class GRIPCommunity(BaseModel):
    """Community cluster representation in GRIP Subgraph."""
    community_id: str
    level: int = 0
    title: Optional[str] = None
    summary: Optional[str] = None
    member_entities: List[str] = Field(default_factory=list)


class GRIPSubgraph(BaseModel):
    """GRIP Contract 2: Canonical Subgraph Object."""
    entities: List[GRIPEntity] = Field(default_factory=list)
    relationships: List[GRIPRelationship] = Field(default_factory=list)
    paths: List[GRIPPath] = Field(default_factory=list)
    communities: List[GRIPCommunity] = Field(default_factory=list)


class GRIPChunkProvenance(BaseModel):
    """Cryptographic chunk hash and provenance metadata."""
    chunk_id: str
    sha256_hash: Optional[str] = None
    source_uri: Optional[str] = None
    retrieval_score: Optional[float] = None
    text_length: Optional[int] = None


class GRIPProvenance(BaseModel):
    """GRIP Contract 5: Cryptographic and Traversal Provenance."""
    chunk_hashes: List[GRIPChunkProvenance] = Field(default_factory=list)
    traversal_depth: Optional[int] = None
    visited_not_cited: List[str] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)


class GRIPTelemetry(BaseModel):
    """Execution telemetry and resource accounting."""
    latency_us: Optional[int] = None
    engine: str = "tigergraph"
    model: Optional[str] = None
    llm_calls: Optional[int] = None
    cost_usd: Optional[float] = None


class GRIPCanonicalEnvelope(BaseModel):
    """GRIP v0.5.0 Canonical Response Envelope."""
    grip_version: str = Field(default=GRIP_SPEC_VERSION)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    modality: GRIPModality
    natural_language_response: str
    answered_question: bool
    subgraph: GRIPSubgraph = Field(default_factory=GRIPSubgraph)
    provenance: GRIPProvenance = Field(default_factory=GRIPProvenance)
    telemetry: GRIPTelemetry = Field(default_factory=GRIPTelemetry)
    raw_query_sources: Optional[Dict[str, Any]] = None


class GRIPAdapter:
    """Pure transformation adapter for converting GraphRAG responses to GRIP v0.5.0 envelopes."""

    @staticmethod
    def compute_sha256(text: Optional[str]) -> Optional[str]:
        """Compute exact SHA-256 over raw chunk text without mutation."""
        if text is None:
            return None
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def determine_modality(cls, query_sources: Optional[Dict[str, Any]]) -> GRIPModality:
        """Map internal tools and execution traces to canonical GRIP modalities."""
        if not query_sources:
            return GRIPModality.AUTO_ROUTED

        plan = query_sources.get("plan")
        tools_used = set()
        if plan and isinstance(plan, dict):
            for step in plan.get("steps", []):
                t = step.get("tool", "")
                if t:
                    tools_used.add(t)

        steps_summary = query_sources.get("steps", [])
        if isinstance(steps_summary, list):
            for s in steps_summary:
                t = s.get("step_id", "")
                if t:
                    tools_used.add(t)

        # Modality Resolution Hierarchy
        if any("temporal_resolve" in t or "temporal" in t for t in tools_used):
            return GRIPModality.TEMPORAL_CAUSAL
        if any("Vector_Search" in t or "hybrid" in t for t in tools_used):
            return GRIPModality.VECTOR_GRAPH_HYBRID
        if any("lookup" in t for t in tools_used):
            return GRIPModality.LOCAL_ENTITY
        if any("superlative" in t or "aggregate" in t for t in tools_used):
            return GRIPModality.DETERMINISTIC_ANALYTIC
        if any("schema" in t or "gsql" in t or "cypher" in t for t in tools_used):
            return GRIPModality.SCHEMA_CYPHER_GSQL

        return GRIPModality.AUTO_ROUTED

    @classmethod
    def extract_subgraph(cls, query_sources: Optional[Dict[str, Any]]) -> GRIPSubgraph:
        """Extract entities and relations faithfully from query_sources without fabrication."""
        entities: List[GRIPEntity] = []
        relationships: List[GRIPRelationship] = []
        paths: List[GRIPPath] = []
        communities: List[GRIPCommunity] = []

        if not query_sources:
            return GRIPSubgraph()

        seen_entities = set()

        def add_entity(entity_id: str, etype: Optional[str] = None, attrs: Optional[Dict] = None):
            if entity_id and entity_id not in seen_entities:
                seen_entities.add(entity_id)
                entities.append(
                    GRIPEntity(
                        id=str(entity_id),
                        type=etype,
                        attributes=attrs or {},
                    )
                )

        # 1. Extract from structured step results if present (richer entity types/attributes)
        results_ctx = query_sources.get("result", {})
        if isinstance(results_ctx, dict):
            structural = results_ctx.get("structural", [])
            for item in structural:
                if isinstance(item, dict):
                    # Check for direct top-level event/entity dictionary
                    item_id = item.get("event_id") or item.get("id") or item.get("event_title") or item.get("title")
                    if item_id:
                        add_entity(str(item_id), item.get("type", "OlympicEvent" if "event" in str(item_id).lower() or "event_title" in item else "Entity"), item)

                    # Check for nested records or candidates
                    if "records" in item and isinstance(item["records"], list):
                        for rec in item["records"]:
                            if isinstance(rec, dict):
                                rid = rec.get("id") or rec.get("event_id") or rec.get("athlete_id") or rec.get("country")
                                if rid:
                                    add_entity(str(rid), rec.get("type", "Record"), rec)
                    if "winner" in item:
                        add_entity(str(item["winner"]), "Winner", {"role": "winner"})
                    if "gold" in item:
                        add_entity(str(item["gold"]), "GoldMedalist", {"role": "gold", "year": item.get("year")})
                    if "candidates" in item and isinstance(item["candidates"], list):
                        for cand in item["candidates"]:
                            if isinstance(cand, dict):
                                cid = cand.get("name") or cand.get("id")
                                if cid:
                                    add_entity(str(cid), "Candidate", cand)

        # 2. Extract from citations
        citations = query_sources.get("citations", [])
        if isinstance(citations, list):
            for cit in citations:
                if isinstance(cit, dict):
                    cid = cit.get("id") or cit.get("chunk_id") or cit.get("document_chunk_id")
                    ctype = cit.get("type") or ("DocumentChunk" if "chunk" in str(cid).lower() else "Entity")
                    if cid:
                        add_entity(str(cid), ctype, cit)
                elif isinstance(cit, str):
                    add_entity(cit, "CitationReference")

        return GRIPSubgraph(
            entities=entities,
            relationships=relationships,
            paths=paths,
            communities=communities,
        )

    @classmethod
    def extract_provenance(cls, query_sources: Optional[Dict[str, Any]]) -> GRIPProvenance:
        """Construct deterministic cryptographic provenance records from retrieved evidence."""
        if not query_sources:
            return GRIPProvenance()

        chunk_hashes: List[GRIPChunkProvenance] = []
        seen_chunks = set()

        citations = query_sources.get("citations", [])
        retrieved_citations = query_sources.get("retrieved_citations", [])

        # Process citations with raw text if available
        if isinstance(citations, list):
            for cit in citations:
                if isinstance(cit, dict):
                    cid = str(cit.get("id") or cit.get("chunk_id") or cit.get("document_chunk_id") or "")
                    if cid and cid not in seen_chunks:
                        seen_chunks.add(cid)
                        text = cit.get("text") or cit.get("chunk_text") or cit.get("content")
                        score = cit.get("score") or cit.get("similarity") or cit.get("rrf_score")
                        uri = cit.get("uri") or cit.get("source_uri") or cit.get("document_id")

                        chunk_hashes.append(
                            GRIPChunkProvenance(
                                chunk_id=cid,
                                sha256_hash=cls.compute_sha256(text) if text else None,
                                source_uri=str(uri) if uri else None,
                                retrieval_score=float(score) if score is not None else None,
                                text_length=len(text) if text else None,
                            )
                        )

        # Process retrieved citations that may not have been cited (visited_not_cited audit)
        visited_not_cited: List[str] = []
        if isinstance(retrieved_citations, list):
            cited_ids = {c.chunk_id for c in chunk_hashes}
            for r_id in retrieved_citations:
                r_id_str = str(r_id)
                if r_id_str not in cited_ids:
                    visited_not_cited.append(r_id_str)

        return GRIPProvenance(
            chunk_hashes=chunk_hashes,
            traversal_depth=None,  # Not inferred unless explicitly logged in step result
            visited_not_cited=visited_not_cited,
            citations=citations if isinstance(citations, list) else [],
        )

    @classmethod
    def from_graphrag_response(
        cls,
        response: GraphRAGResponse,
        request_id: Optional[str] = None,
        latency_us: Optional[int] = None,
        llm_calls: Optional[int] = None,
        cost_usd: Optional[float] = None,
        engine: str = "tigergraph",
    ) -> GRIPCanonicalEnvelope:
        """Convert a completed GraphRAGResponse into a GRIP v0.5.0 canonical envelope."""
        qs = response.query_sources or {}

        modality = cls.determine_modality(qs)
        subgraph = cls.extract_subgraph(qs)
        provenance = cls.extract_provenance(qs)

        telemetry = GRIPTelemetry(
            latency_us=latency_us,
            engine=engine,
            model=None,
            llm_calls=llm_calls,
            cost_usd=cost_usd,
        )

        return GRIPCanonicalEnvelope(
            grip_version=GRIP_SPEC_VERSION,
            request_id=request_id or str(uuid.uuid4()),
            modality=modality,
            natural_language_response=response.natural_language_response,
            answered_question=response.answered_question,
            subgraph=subgraph,
            provenance=provenance,
            telemetry=telemetry,
            raw_query_sources=qs,
        )

    @classmethod
    def to_json(cls, envelope: GRIPCanonicalEnvelope, indent: Optional[int] = 2) -> str:
        """Deterministic JSON serialization helper."""
        return envelope.model_dump_json(indent=indent)
