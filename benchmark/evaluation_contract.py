# Copyright (c) 2024-2026 TigerGraph, Inc.
# Unified Three-Way Evaluation Contract Specification

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json

@dataclass
class CanonicalEvaluationRecord:
    """
    Canonical record schema for unified evaluation across RAG, GraphRAG, and Agentic GraphRAG.
    Unavailable metrics must be explicitly represented as None (N/A). Never fabricate values.
    """
    qid: str
    qtype: str
    prediction: str
    gold: str
    correctness: bool
    completeness: Optional[float] = None
    grounding: Optional[float] = None
    total_tokens: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    citations: List[Any] = field(default_factory=list)
    retrieval_methods: List[str] = field(default_factory=list)
    retrieval_steps: int = 1
    tools: List[str] = field(default_factory=list)
    specialist_agents: List[str] = field(default_factory=list)
    strategy_changes: int = 0
    stop_reason: str = "completed"
    retries: int = 0
    agent_steps: Optional[List[Any]] = None
    budget_usage: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalEvaluationRecord":
        return cls(**data)
