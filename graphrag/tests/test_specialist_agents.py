# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# Unit and Integration Test Suite for Specialist Agent Capability Layer

import os
import sys
import json
import logging
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.specialists import (
    SpecialistAgent,
    EntityLinkingSpecialist,
    SimilarityRetrievalSpecialist,
    DocumentRetrievalSpecialist,
    GraphTraversalSpecialist,
    AnalyticalSpecialist,
    MultiHopInvestigationSpecialist,
    EvidenceEvaluationSpecialist,
    SpecialistOrchestrator,
    SpecialistOutput,
    SpecialistTelemetry
)
from pyTigerGraph import TigerGraphConnection

class StandaloneCtx:
    def __init__(self, conn):
        self.conn = conn

    def emit(self, msg):
        pass


class TestSpecialistAgents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "configs", "local_server_config.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "configs", "local_server_config.json"),
            "configs/local_server_config.json"
        ]
        cfg_path = next((c for c in cfg_candidates if os.path.exists(c)), None)
        assert cfg_path is not None, "Could not find local_server_config.json"

        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)["db_config"]

        cls.conn = TigerGraphConnection(
            host=cfg["hostname"],
            graphname=cfg["graphname"],
            username=cfg["username"],
            password=cfg["password"],
            restppPort=cfg["restppPort"],
            gsPort=cfg["gsPort"],
        )
        cls.conn.getToken()
        cls.ctx = StandaloneCtx(cls.conn)
        cls.orchestrator = SpecialistOrchestrator()

    # --------------------------------------------------------------------------
    # INDEPENDENT SPECIALIST TESTS
    # --------------------------------------------------------------------------
    def test_01_entity_linking_specialist(self):
        spec = EntityLinkingSpecialist()
        out = spec.execute("link_event", {"query": "How many nations competed in Sailing at the 2016 Summer Olympics \u2013 Women's RS:X?"}, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(spec.name, "EntityLinkingSpecialist")
        self.assertIn("linked_entity", out.context)
        self.assertEqual(out.telemetry.recommendation, "continue")
        self.assertIsNotNone(out.telemetry.latency_ms)

    def test_02_similarity_retrieval_specialist(self):
        spec = SimilarityRetrievalSpecialist()
        out = spec.execute("search", {"query": "Biathlon Winter Olympics", "top_k": 3}, self.ctx)
        self.assertEqual(spec.name, "SimilarityRetrievalSpecialist")
        self.assertIn("SimilarityRetrievalSpecialist", out.telemetry.specialist_name)
        self.assertIsNotNone(out.telemetry.latency_ms)

    def test_03_document_retrieval_specialist(self):
        spec = DocumentRetrievalSpecialist()
        out = spec.execute("fetch", {"doc_ids": ["Q47091419"], "chunk_ids": ["doc1_c1"]}, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(spec.name, "DocumentRetrievalSpecialist")
        self.assertEqual(out.context["doc_ids"], ["Q47091419"])
        self.assertEqual(out.telemetry.recommendation, "continue")

    def test_04_graph_traversal_specialist(self):
        spec = GraphTraversalSpecialist()
        out = spec.execute("lookup", {"event_title": "Sailing at the 2016 Summer Olympics \u2013 Women's RS:X"}, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(spec.name, "GraphTraversalSpecialist")
        self.assertEqual(str(out.summary), "26")
        self.assertEqual(out.telemetry.recommendation, "answer_ready")
        self.assertEqual(out.telemetry.tool_used, "graphrag__lookup")

    def test_05_analytical_specialist(self):
        spec = AnalyticalSpecialist()
        # Aggregate
        out_agg = spec.execute("aggregate", {"sport": "biathlon", "games": "2018 Winter Olympics", "threshold": 73}, self.ctx)
        self.assertTrue(out_agg.ok)
        self.assertEqual(str(out_agg.summary), "5")
        self.assertEqual(out_agg.telemetry.tool_used, "graphrag__aggregate")

        # Superlative
        out_sup = spec.execute("superlative", {"sport": "alpine skiing", "games": "2014 Winter Olympics"}, self.ctx)
        self.assertTrue(out_sup.ok)
        self.assertIn("Men's slalom", out_sup.summary)
        self.assertEqual(out_sup.telemetry.tool_used, "graphrag__superlative")

    def test_06_multi_hop_investigation_specialist(self):
        spec = MultiHopInvestigationSpecialist()
        out = spec.execute("temporal_resolve", {
            "event_name": "men's freestyle 82 kg wrestling",
            "season": "Summer",
            "reference_year": 1996,
            "direction": "immediately before"
        }, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(spec.name, "MultiHopInvestigationSpecialist")
        self.assertEqual(out.summary, "Kevin Jackson")
        self.assertEqual(out.telemetry.tool_used, "graphrag__temporal_resolve")
        self.assertEqual(out.telemetry.recommendation, "answer_ready")

    def test_07_evidence_evaluation_specialist(self):
        spec = EvidenceEvaluationSpecialist()
        out = spec.execute("evaluate_evidence", {
            "prediction": "Kevin Jackson",
            "evidence": {"winner": "Kevin Jackson", "year": 1992},
            "citations": ["temporal_resolve"]
        }, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(spec.name, "EvidenceEvaluationSpecialist")
        self.assertTrue(out.context["grounded"])
        self.assertEqual(out.telemetry.recommendation, "stop")

    # --------------------------------------------------------------------------
    # END-TO-END ORCHESTRATION TESTS (QUESTION -> ORCHESTRATOR -> SPECIALIST -> RESULT)
    # --------------------------------------------------------------------------
    def test_08_e2e_lookup_orchestration(self):
        q = "How many nations competed in Sailing at the 2016 Summer Olympics \u2013 Women's RS:X?"
        parsed_args = {"event_title": "Sailing at the 2016 Summer Olympics \u2013 Women's RS:X"}
        out, telemetries = self.orchestrator.route_question("lookup", q, parsed_args, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(str(out.summary), "26")
        self.assertEqual(len(telemetries), 3)  # EntityLinking -> GraphTraversal -> EvidenceEval
        self.assertEqual(telemetries[0].specialist_name, "EntityLinkingSpecialist")
        self.assertEqual(telemetries[1].specialist_name, "GraphTraversalSpecialist")
        self.assertEqual(telemetries[2].specialist_name, "EvidenceEvaluationSpecialist")

    def test_09_e2e_aggregation_orchestration(self):
        q = "How many biathlon events at the 2018 Winter Olympics had more than 73 competitors?"
        parsed_args = {"sport": "biathlon", "games": "2018 Winter Olympics", "threshold": 73}
        out, telemetries = self.orchestrator.route_question("aggregation", q, parsed_args, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(str(out.summary), "5")
        self.assertEqual(len(telemetries), 2)  # Analytical -> EvidenceEval
        self.assertEqual(telemetries[0].specialist_name, "AnalyticalSpecialist")
        self.assertEqual(telemetries[1].specialist_name, "EvidenceEvaluationSpecialist")

    def test_10_e2e_temporal_orchestration(self):
        q = "Who won the gold medal in the men's freestyle 82 kg wrestling event at the Summer Olympics held immediately before 1996?"
        parsed_args = {
            "event_name": "men's freestyle 82 kg wrestling",
            "season": "Summer",
            "reference_year": 1996,
            "direction": "immediately before"
        }
        out, telemetries = self.orchestrator.route_question("temporal", q, parsed_args, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(out.summary, "Kevin Jackson")
        self.assertEqual(len(telemetries), 2)  # MultiHop -> EvidenceEval
        self.assertEqual(telemetries[0].specialist_name, "MultiHopInvestigationSpecialist")
        self.assertEqual(telemetries[1].specialist_name, "EvidenceEvaluationSpecialist")

    def test_11_e2e_superlative_orchestration(self):
        q = "Which alpine skiing event at the 2014 Winter Olympics had the highest number of competitors?"
        parsed_args = {"sport": "alpine skiing", "games": "2014 Winter Olympics"}
        out, telemetries = self.orchestrator.route_question("superlative", q, parsed_args, self.ctx)
        self.assertTrue(out.ok)
        self.assertIn("Men's slalom", out.summary)
        self.assertEqual(len(telemetries), 2)  # Analytical -> EvidenceEval
        self.assertEqual(telemetries[0].specialist_name, "AnalyticalSpecialist")
        self.assertEqual(telemetries[1].specialist_name, "EvidenceEvaluationSpecialist")

    def test_12_e2e_multi_hop_orchestration(self):
        q = "Who won the gold medal in the men's 20 kilometres walk event at the Summer Olympics held immediately before 2016?"
        parsed_args = {
            "event_name": "men's 20 kilometres walk",
            "season": "Summer",
            "reference_year": 2016,
            "direction": "immediately before"
        }
        out, telemetries = self.orchestrator.route_question("multi_hop", q, parsed_args, self.ctx)
        self.assertTrue(out.ok)
        self.assertEqual(out.summary, "Chen Ding")
        self.assertEqual(telemetries[0].specialist_name, "MultiHopInvestigationSpecialist")


if __name__ == "__main__":
    unittest.main()
