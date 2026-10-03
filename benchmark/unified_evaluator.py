# Copyright (c) 2024-2026 TigerGraph, Inc.
# Unified Evaluator Engine for RAG, GraphRAG, and Agentic GraphRAG

import re
import string
from typing import Dict, Any, List, Optional
from benchmark.evaluation_contract import CanonicalEvaluationRecord

_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}
_UNITS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9
}

_WORD_NUMBERS = {}
for _t_word, _t_val in _TENS.items():
    for _u_word, _u_val in _UNITS.items():
        _WORD_NUMBERS[f"{_t_word} {_u_word}"] = str(_t_val + _u_val)
        _WORD_NUMBERS[f"{_t_word}-{_u_word}"] = str(_t_val + _u_val)

_WORD_NUMBERS.update({
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
    "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
    "eighty": "80", "ninety": "90", "hundred": "100"
})

def normalize_answer(s: str) -> str:
    """Normalize string for exact/substring matching, converting number words to digits."""
    if not s:
        return ""
    def split_camel_case(text):
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', str(text))
    def lower(text):
        return str(text).lower()
    def normalize_dashes(text):
        return re.sub(r'[\-\u2010\u2011\u2012\u2013\u2014\u2015]', ' ', text)
    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)
    def convert_word_numbers(text):
        for word, num in _WORD_NUMBERS.items():
            text = re.sub(rf'\b{word}\b', num, text, flags=re.IGNORECASE)
        return text
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)
    def white_space_fix(text):
        return ' '.join(text.split())

    text = split_camel_case(s)
    text = lower(text)
    text = normalize_dashes(text)
    text = remove_punc(text)
    text = convert_word_numbers(text)
    text = remove_articles(text)
    return white_space_fix(text)

def compute_correctness(prediction: str, gold: str) -> bool:
    """Deterministic correctness check via normalized substring / exact matching with token boundary safety."""
    norm_pred = normalize_answer(prediction)
    norm_gold = normalize_answer(gold)
    if not norm_gold or not norm_pred:
        return False
    if norm_gold == norm_pred:
        return True
    pattern_gold = rf'\b{re.escape(norm_gold)}\b'
    pattern_pred = rf'\b{re.escape(norm_pred)}\b'
    if re.search(pattern_gold, norm_pred) or re.search(pattern_pred, norm_gold):
        return True
    gold_tokens = norm_gold.split()
    if len(gold_tokens) > 1 and all(re.search(rf'\b{re.escape(tok)}\b', norm_pred) for tok in gold_tokens):
        return True
    return False

def compute_completeness(prediction: str, gold: str) -> float:
    """
    Deterministic/reproducible completeness metric without an LLM judge.
    Calculates word-level overlap ratio of gold answer tokens present in prediction.
    """
    norm_pred = normalize_answer(prediction)
    norm_gold = normalize_answer(gold)
    if not norm_gold:
        return 0.0
    gold_tokens = norm_gold.split()
    if not gold_tokens:
        return 0.0
    hits = sum(1 for tok in gold_tokens if tok in norm_pred)
    return round(hits / len(gold_tokens), 4)

def compute_grounding(prediction: str, context_texts: List[str]) -> Optional[float]:
    """
    Deterministic grounding metric.
    Calculates ratio of prediction non-stopword tokens found in retrieved context.
    Returns None if no text context was retrieved (e.g. N/A for pure graph tools).
    """
    if not context_texts:
        return None
    joined_context = normalize_answer(" ".join(context_texts))
    if not joined_context:
        return None
    norm_pred = normalize_answer(prediction)
    pred_tokens = [tok for tok in norm_pred.split() if len(tok) > 2]
    if not pred_tokens:
        return 1.0
    hits = sum(1 for tok in pred_tokens if tok in joined_context)
    return round(hits / len(pred_tokens), 4)

def compute_retrieval_intrusion(retrieved_chunk_ids: List[str], gold_chunk_ids: List[str]) -> Optional[float]:
    """
    Computes percentage of retrieved text chunks that are distractors/irrelevant.
    Returns None if retrieved_chunk_ids is empty or N/A.
    """
    if not retrieved_chunk_ids:
        return None
    gold_set = set(g.upper() for g in gold_chunk_ids)
    distractors = sum(1 for cid in retrieved_chunk_ids if cid.upper() not in gold_set)
    return round((distractors / len(retrieved_chunk_ids)) * 100.0, 2)

class UnifiedEvaluator:
    """Evaluates raw records from RAG, GraphRAG, or Agentic GraphRAG into CanonicalEvaluationRecord."""

    @staticmethod
    def parse_raw_record(raw: Dict[str, Any], pipeline_type: str = "agentic") -> CanonicalEvaluationRecord:
        qid = str(raw.get("qid", ""))
        qtype = str(raw.get("qtype", ""))
        prediction = str(raw.get("prediction") or raw.get("generated_answer") or raw.get("final_answer") or "")
        gold = str(raw.get("gold") or raw.get("gold_answer") or "")
        
        # Check timeout / error
        is_timeout = bool(raw.get("error") or raw.get("timeout") or "timeout" in str(raw.get("raw_error", "")).lower())
        stop_reason = "timeout" if is_timeout else ("error" if raw.get("error") else "completed")

        # Correctness
        if "normalized_match" in raw:
            correctness = bool(raw["normalized_match"])
        else:
            correctness = compute_correctness(prediction, gold)

        # Completeness
        completeness = compute_completeness(prediction, gold) if prediction else 0.0

        # Latency (convert to ms)
        lat = raw.get("latency") or raw.get("latency_seconds") or raw.get("execution_time")
        latency_ms = round(float(lat) * 1000.0, 2) if lat is not None else None

        # Token usage
        token_usage = raw.get("token_usage") or {}
        total_tokens = token_usage.get("total_tokens")
        input_tokens = token_usage.get("prompt_tokens") or token_usage.get("input_tokens")
        output_tokens = token_usage.get("completion_tokens") or token_usage.get("output_tokens")

        # Retrieval & Evidence
        retrieved_chunks = raw.get("retrieved_chunk_ids") or []
        gold_chunks = raw.get("gold_chunk_ids") or raw.get("gold_doc_ids") or []
        citations = raw.get("citations") or []

        # Grounding
        context_texts = raw.get("retrieved_context_texts") or []
        grounding = compute_grounding(prediction, context_texts)

        # Retrieval Intrusion
        intrusion = raw.get("retrieval_intrusion_at_k")
        if intrusion is None:
            intrusion = compute_retrieval_intrusion(retrieved_chunks, gold_chunks)

        # Evidence breakdown
        evidence_data = {
            "gold_chunk_hit": bool(raw.get("gold_chunk_hit", False)),
            "gold_vertex_hit": bool(raw.get("gold_vertex_hit", False)),
            "gold_tool_evidence_hit": bool(raw.get("gold_tool_evidence_hit", False)),
            "cited_gold_hit": bool(raw.get("cited_gold_hit", False)),
            "gold_combined_hit": bool(raw.get("gold_doc_hit", raw.get("gold_retrieval_hit", False))),
            "retrieval_intrusion_pct": intrusion
        }

        # Tools & Routing
        tools_used = raw.get("deterministic_tools_used") or raw.get("tools_used") or []
        plan_steps = raw.get("plan_steps") or raw.get("plan", [])
        retrieval_steps = len(plan_steps) if plan_steps else (1 if tools_used or retrieved_chunks else 0)
        
        retrieval_methods = []
        if tools_used:
            retrieval_methods.extend(tools_used)
        if retrieved_chunks or raw.get("rag_method") == "hybridsearch" or raw.get("executed_query"):
            retrieval_methods.append("hybrid_vector_graph" if pipeline_type == "graphrag" else "vector_similarity")

        strategy_changes = raw.get("strategy_changes", 0)
        specialist_agents = raw.get("specialist_agents") or (["planner", "executor", "synthesizer"] if pipeline_type == "agentic" else [])
        retries = raw.get("retries", 0)
        agent_steps = raw.get("agent_steps") or raw.get("plan")
        budget_usage = raw.get("budget_usage") or ({
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms
        } if total_tokens is not None or latency_ms is not None else None)

        return CanonicalEvaluationRecord(
            qid=qid,
            qtype=qtype,
            prediction=prediction,
            gold=gold,
            correctness=correctness,
            completeness=completeness,
            grounding=grounding,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            evidence=evidence_data,
            citations=citations,
            retrieval_methods=retrieval_methods,
            retrieval_steps=retrieval_steps,
            tools=tools_used,
            specialist_agents=specialist_agents,
            strategy_changes=strategy_changes,
            stop_reason=stop_reason,
            retries=retries,
            agent_steps=agent_steps,
            budget_usage=budget_usage
        )
