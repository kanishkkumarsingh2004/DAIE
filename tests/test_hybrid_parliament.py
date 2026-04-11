import pytest
from unittest.mock import AsyncMock, MagicMock
from daie.agents.hybrid_parliament import HybridParliamentOrchestrator
from daie.agents.parliament import Parliament
from daie.agents.orchestrator import OrchestratorAgent


class TestHybridParliamentOrchestrator:

    @pytest.fixture
    def mock_parliament(self):
        parliament = MagicMock(spec=Parliament)
        parliament.deliberate = AsyncMock()
        return parliament

    @pytest.fixture
    def mock_orchestrator(self):
        orchestrator = MagicMock(spec=OrchestratorAgent)
        orchestrator.decompose_and_execute = AsyncMock()
        return orchestrator

    @pytest.mark.asyncio
    async def test_hybrid_execution_success(self, mock_parliament, mock_orchestrator):
        """Test successful strategic roadmap execution loop."""

        # Parliament safely abstracts a 90% confidence response
        mock_parliament.deliberate.return_value = {
            "final_answer": "1. Scrape metrics. 2. Write graph.",
            "consensus_confidence": 92.5,
            "reasoning": "High alignment",
        }

        # Orchestrator finishes executing delegative pipeline cleanly
        mock_orchestrator.decompose_and_execute.return_value = "Delegation Successful."

        hybrid_pipeline = HybridParliamentOrchestrator(
            parliament=mock_parliament, orchestrator=mock_orchestrator
        )

        result = await hybrid_pipeline.execute("Analyze budget")

        # Assertions
        assert result == "Delegation Successful."
        mock_parliament.deliberate.assert_called_once()
        mock_orchestrator.decompose_and_execute.assert_called_once()

        # Verify execution context strings
        exec_call_arg = mock_orchestrator.decompose_and_execute.call_args[0][0]
        assert "Analyze budget" in exec_call_arg
        assert "1. Scrape metrics" in exec_call_arg

    @pytest.mark.asyncio
    async def test_hybrid_aborts_on_low_confidence(self, mock_parliament, mock_orchestrator):
        """Test that falling under the safety threshold cleanly halts execution variables."""

        # Parliament fails internally and only yields 40% confidence.
        mock_parliament.deliberate.return_value = {
            "final_answer": "I don't know what the budget is.",
            "consensus_confidence": 42.0,
            "reasoning": "Complete confusion.",
        }

        hybrid_pipeline = HybridParliamentOrchestrator(
            parliament=mock_parliament,
            orchestrator=mock_orchestrator,
            min_confidence_threshold=60.0,
        )

        result = await hybrid_pipeline.execute("Analyze budget")

        assert "aborted" in result
        assert "42.0%" in result

        mock_parliament.deliberate.assert_called_once()
        # Orchestrator is NEVER accessed
        mock_orchestrator.decompose_and_execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_hybrid_gracefully_handles_malformed_consensus(
        self, mock_parliament, mock_orchestrator
    ):
        """Test that malformed string returns from disabled architectures prevent orchestration pipeline breakdown."""

        # Returns a raw string instead of the strict Pydantic dictionary
        mock_parliament.deliberate.return_value = "Raw invalid return string."

        hybrid_pipeline = HybridParliamentOrchestrator(
            parliament=mock_parliament, orchestrator=mock_orchestrator
        )

        result = await hybrid_pipeline.execute("Analyze budget")

        assert "failed to return a structured consensus" in result
        mock_orchestrator.decompose_and_execute.assert_not_called()
