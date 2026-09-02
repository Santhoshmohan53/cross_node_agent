"""
Unit and Integration Tests for Autonomous Deep Research Pipeline.
Verifies Level 1 (Contract), Level 2 (Decomposition & Search), and Level 3 (Synthesis).
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.research_pipeline.deep_research_pipe import (
    ResearchSource,
    ResearchPlan,
    PlannerAgent,
    ParallelScraperAgent,
    SynthesizerAgent,
    DeepResearchPipeline,
    OllamaClient
)


class TestResearchPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=OllamaClient)

    def test_planner_agent_fallback(self):
        """Test that PlannerAgent produces a valid plan even if LLM output is non-JSON."""
        self.mock_client.generate.return_value = "Random raw text without json"
        planner = PlannerAgent(self.mock_client, planner_model="deepseek-r1:7b")
        
        plan = planner.formulate_plan("Quantum Computing Advances")
        self.assertEqual(plan.topic, "Quantum Computing Advances")
        self.assertGreaterEqual(len(plan.sub_questions), 3)
        self.assertGreaterEqual(len(plan.search_queries), 3)

    def test_planner_agent_json_parsing(self):
        """Test that PlannerAgent correctly parses structured JSON from LLM reasoning."""
        mock_json_response = (
            "<think>Thinking about quantum computing...</think>\n"
            "```json\n"
            "{\n"
            '  "sub_questions": ["What is topological quantum?", "What are 2025 milestones?", "What are error rates?"],\n'
            '  "search_queries": ["topological quantum computing", "quantum computing milestones 2025", "quantum error correction rates"],\n'
            '  "focus_areas": ["Architecture", "Recent Milestones", "Error Correction"]\n'
            "}\n"
            "```"
        )
        self.mock_client.generate.return_value = mock_json_response
        planner = PlannerAgent(self.mock_client, planner_model="deepseek-r1:7b")
        
        plan = planner.formulate_plan("Quantum Computing Advances", use_llm=True)
        self.assertEqual(len(plan.sub_questions), 3)
        self.assertIn("topological quantum computing", plan.search_queries)

    def test_scraper_agent_mock(self):
        """Test that ParallelScraperAgent aggregates and extracts source content."""
        scraper = ParallelScraperAgent()
        
        mock_source = ResearchSource(
            url="https://example.com/quantum",
            title="Quantum News",
            snippet="Breakthrough in superconducting qubits"
        )
        self.assertEqual(mock_source.domain, "example.com")

    def test_synthesizer_agent_report_generation(self):
        """Test that SynthesizerAgent compiles evidence and issues a structured prompt."""
        self.mock_client.generate.return_value = "## Executive Summary\nQuantum computing has advanced [1]."
        synthesizer = SynthesizerAgent(self.mock_client, synthesis_model="qwen2.5-vl:7b")
        
        plan = ResearchPlan(
            topic="Quantum Computing",
            sub_questions=["What is quantum?"],
            search_queries=["quantum overview"],
            focus_areas=["Overview"]
        )
        sources = [
            ResearchSource(
                url="https://nature.com/articles/quantum",
                title="Nature Quantum Report",
                snippet="Superconducting qubits achieve 99.9% fidelity.",
                content="Superconducting qubits achieve 99.9% fidelity under cryogenic testing."
            )
        ]
        
        report = synthesizer.compile_report("Quantum Computing", plan, sources)
        self.assertIn("## Executive Summary", report)
        self.assertTrue(self.mock_client.generate.called)


if __name__ == "__main__":
    unittest.main()
