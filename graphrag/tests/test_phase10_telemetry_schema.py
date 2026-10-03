# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# Phase 10 Offline Schema Test for Agentic Effectiveness Telemetry

import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/code")

from agent.specialists import AgenticEffectivenessTelemetry, build_effectiveness_telemetry

class TestPhase10TelemetrySchema(unittest.TestCase):
    """Validates the schema completeness, no-secret policy, and no chain-of-thought constraint."""

    def test_all_19_required_fields_present(self):
        mock_exec_res = {
            "ok": True,
            "initial_strategy": "Pattern A: Entity Linking -> Graph Traversal -> Answer",
            "specialists_invoked": ["EntityLinkingSpecialist", "GraphTraversalSpecialist"],
            "strategy_changes": 0,
            "reason_for_change": None,
            "evidence_before": {"linked_entity": "Men's 100m"},
            "evidence_after": {"matched_event": "Men's 100m", "result": "18"},
            "stop_reason": "answer_found",
            "total_steps": 2,
            "final_answer": "18",
            "telemetry_trail": [
                {
                    "specialist_name": "EntityLinkingSpecialist",
                    "action": "link_event",
                    "input_summary": "query='Men's 100m'",
                    "tool_used": None,
                    "result_summary": "Linked entity: 'Men's 100m'",
                    "latency_ms": 1.5,
                    "recommendation": "continue"
                },
                {
                    "specialist_name": "GraphTraversalSpecialist",
                    "action": "lookup",
                    "input_summary": "event_title='Men's 100m'",
                    "tool_used": "graphrag__lookup",
                    "result_summary": "18",
                    "latency_ms": 12.4,
                    "recommendation": "answer_ready"
                }
            ]
        }

        rec = build_effectiveness_telemetry(
            qid="test-qid-001",
            exec_res=mock_exec_res,
            gold="18",
            latency_ms=13.9,
            token_usage={"input_tokens": 120, "output_tokens": 15, "total_tokens": 135}
        )

        d = rec.to_dict()

        # Required 19 top-level fields
        required_fields = [
            "qid",
            "pipeline",
            "accuracy",
            "completeness",
            "grounding",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "latency_ms",
            "steps",
            "retrieval_methods",
            "specialists_invoked",
            "tools_called",
            "chunks_retrieved",
            "citations",
            "strategy_changes",
            "stop_reason",
            "budget_limit",
            "budget_used"
        ]

        for rf in required_fields:
            self.assertIn(rf, d, f"Missing required telemetry field: {rf}")

        # Field validation
        self.assertEqual(d["qid"], "test-qid-001")
        self.assertEqual(d["pipeline"], "agentic_graphrag")
        self.assertTrue(d["accuracy"])
        self.assertEqual(d["completeness"], 1.0)
        self.assertEqual(d["steps"], 2)
        self.assertEqual(d["stop_reason"], "answer_found")
        self.assertEqual(d["budget_limit"]["max_llm_calls"], 6)
        self.assertEqual(d["budget_used"]["steps"], 2)

        # JSON Serialization check
        json_str = json.dumps(d, indent=2)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["qid"], "test-qid-001")

        # No secret check
        secrets = ["sk-", "Bearer", "password", "SECRET", "PRIVATE KEY", "api_key"]
        for s in secrets:
            self.assertNotIn(s, json_str)

        # No chain of thought check
        cot_markers = ["Let's think", "Step 1: I will", "Thinking Process:", "scratchpad", "internal monologue"]
        for cot in cot_markers:
            self.assertNotIn(cot, json_str)


if __name__ == "__main__":
    unittest.main()
