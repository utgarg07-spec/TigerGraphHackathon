# Copyright (c) 2024-2026 TigerGraph, Inc.
# Offline Test Suite for Unified Evaluator

import unittest
import json
from benchmark.evaluation_contract import CanonicalEvaluationRecord
from benchmark.unified_evaluator import UnifiedEvaluator, compute_correctness, compute_completeness, compute_grounding, compute_retrieval_intrusion

class TestUnifiedEvaluator(unittest.TestCase):

    def test_1_exact_correct_answer(self):
        pred = "The first modern Olympic Games held in 1896 had 26 nations."
        gold = "26 nations"
        rec = UnifiedEvaluator.parse_raw_record({
            "qid": "test-001",
            "qtype": "lookup",
            "prediction": pred,
            "gold": gold,
            "latency_seconds": 1.5,
            "deterministic_tools_used": ["graphrag__lookup"],
            "gold_doc_hit": True
        }, pipeline_type="agentic")

        self.assertTrue(rec.correctness)
        self.assertEqual(rec.completeness, 1.0)
        self.assertEqual(rec.latency_ms, 1500.0)
        self.assertEqual(rec.stop_reason, "completed")
        self.assertIn("graphrag__lookup", rec.tools)

    def test_2_incorrect_answer(self):
        pred = "Joachim Kunz"
        gold = "Naim Süleymanoğlu"
        rec = UnifiedEvaluator.parse_raw_record({
            "qid": "test-002",
            "qtype": "multi_hop",
            "prediction": pred,
            "gold": gold,
            "latency_seconds": 3.2,
            "gold_doc_hit": False
        }, pipeline_type="rag")

        self.assertFalse(rec.correctness)
        self.assertEqual(rec.completeness, 0.0)
        self.assertFalse(rec.evidence["gold_combined_hit"])

    def test_3_evidence_hit(self):
        raw = {
            "qid": "test-003",
            "qtype": "aggregation",
            "prediction": "5",
            "gold": "5",
            "gold_doc_hit": True,
            "gold_tool_evidence_hit": True,
            "deterministic_tools_used": ["graphrag__aggregate"]
        }
        rec = UnifiedEvaluator.parse_raw_record(raw, pipeline_type="agentic")
        self.assertTrue(rec.evidence["gold_combined_hit"])
        self.assertTrue(rec.evidence["gold_tool_evidence_hit"])

    def test_4_evidence_miss(self):
        raw = {
            "qid": "test-004",
            "qtype": "multi_hop",
            "prediction": "Unknown",
            "gold": "London Velopark",
            "gold_doc_hit": False,
            "gold_chunk_hit": False
        }
        rec = UnifiedEvaluator.parse_raw_record(raw, pipeline_type="rag")
        self.assertFalse(rec.evidence["gold_combined_hit"])
        self.assertFalse(rec.evidence["gold_chunk_hit"])

    def test_5_na_metric_handling(self):
        raw = {
            "qid": "test-005",
            "qtype": "lookup",
            "prediction": "Athens",
            "gold": "Athens",
            "deterministic_tools_used": ["graphrag__lookup"]
        }
        rec = UnifiedEvaluator.parse_raw_record(raw, pipeline_type="agentic")
        # Grounding and intrusion are N/A (None) when no raw text chunks/contexts are retrieved
        self.assertIsNone(rec.grounding)
        self.assertIsNone(rec.evidence["retrieval_intrusion_pct"])
        self.assertIsNone(rec.total_tokens)

    def test_6_timeout_case(self):
        raw = {
            "qid": "pub-015",
            "qtype": "multi_hop",
            "prediction": "",
            "gold": "Gold Medalist",
            "error": "Request Exception: Read timed out. (read timeout=120)",
            "timeout": True
        }
        rec = UnifiedEvaluator.parse_raw_record(raw, pipeline_type="agentic")
        self.assertFalse(rec.correctness)
        self.assertEqual(rec.stop_reason, "timeout")

    def test_7_agentic_trace(self):
        raw = {
            "qid": "pub-002",
            "qtype": "temporal",
            "prediction": "Chen Ding",
            "gold": "Chen Ding",
            "plan_steps": [{"id": "S1", "tool": "graphrag__temporal_resolve"}],
            "deterministic_tools_used": ["graphrag__temporal_resolve"],
            "token_usage": {"total_tokens": 450, "prompt_tokens": 350, "completion_tokens": 100},
            "latency_seconds": 4.96
        }
        rec = UnifiedEvaluator.parse_raw_record(raw, pipeline_type="agentic")
        self.assertEqual(rec.retrieval_steps, 1)
        self.assertEqual(rec.total_tokens, 450)
        self.assertEqual(rec.input_tokens, 350)
        self.assertEqual(rec.output_tokens, 100)
        self.assertIn("planner", rec.specialist_agents)

    def test_8_non_agentic_trace(self):
        raw = {
            "qid": "pub-001",
            "qtype": "aggregation",
            "prediction": "18",
            "gold": "26",
            "retrieved_chunk_ids": ["chunk_1", "chunk_2"],
            "gold_doc_ids": ["chunk_99"],
            "latency_seconds": 1.2
        }
        rec = UnifiedEvaluator.parse_raw_record(raw, pipeline_type="rag")
        self.assertEqual(rec.specialist_agents, [])
        self.assertEqual(rec.retrieval_steps, 1)
        self.assertEqual(rec.evidence["retrieval_intrusion_pct"], 100.0)

if __name__ == "__main__":
    unittest.main()
