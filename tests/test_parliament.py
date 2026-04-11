"""
Tests for the Parliament mixture-of-agents architecture.
"""

from unittest.mock import AsyncMock, MagicMock
import pytest

from daie.agents.agent import Agent
from daie.agents.config import AgentConfig
from daie.agents.parliament import Parliament


@pytest.fixture
def mock_agents():
    """Fixture providing a list of configured mock agents."""
    agents = []
    for i in range(3):
        agent = MagicMock(spec=Agent)
        agent.name = f"MockAgent_{i}"
        agent.config = AgentConfig(name=f"MockAgent_{i}")

        # Async methods
        agent.execute_task = AsyncMock(return_value=f"Answer from agent {i}")
        agent.start = AsyncMock()
        agent.stop = AsyncMock()

        agents.append(agent)
    return agents


class TestParliament:

    def test_initialization(self, mock_agents):
        """Test basic parliament initialization."""
        parliament = Parliament(sub_agents=mock_agents)
        assert len(parliament.sub_agents) == 3
        # By default, Speaker is the first agent
        assert parliament.speaker == mock_agents[0]
        assert parliament.max_review_rounds == 1

    def test_initialization_with_fewer_than_two_agents(self, mock_agents):
        """Test parliament rejects fewer than two sub-agents."""
        with pytest.raises(ValueError, match="Parliament needs at least 2 agents"):
            Parliament(sub_agents=[mock_agents[0]])

    def test_build_review_prompt(self, mock_agents):
        """Test that the review prompt correctly aggregates other answers."""
        parliament = Parliament(sub_agents=mock_agents)

        other_answers = [
            {"agent_id": 1, "answer": "The sky is blue"},
            {"agent_id": 2, "answer": "Water is wet"},
        ]

        review_prompt = parliament._build_review_prompt("What are facts?", other_answers)

        assert "What are facts?" in review_prompt
        assert "Agent 1 answer:\nThe sky is blue" in review_prompt
        assert "Agent 2 answer:\nWater is wet" in review_prompt
        assert "Do NOT review yourself" in review_prompt

    def test_build_synthesis_prompt(self, mock_agents):
        """Test that the synthesis prompt correctly bundles answers and reviews."""
        parliament = Parliament(sub_agents=mock_agents)

        initial_answers = [{"agent_id": 0, "answer": "A"}, {"agent_id": 1, "answer": "B"}]

        reviews = [
            "A is correct",  # Review from Agent 0
            Exception("Simulated Failure"),  # Failed review from Agent 1
        ]

        synth_prompt = parliament._build_synthesis_prompt("Question", initial_answers, reviews)

        assert "Question" in synth_prompt
        assert "Agent 0: A" in synth_prompt
        assert "Review from Agent 0: A is correct" in synth_prompt
        assert "Review from Agent 1: [Review failed]" in synth_prompt

    @pytest.mark.asyncio
    async def test_start_and_stop(self, mock_agents):
        """Test starting and stopping delegates to all sub-agents."""
        parliament = Parliament(sub_agents=mock_agents)

        await parliament.start()
        for agent in mock_agents:
            agent.start.assert_called_once()

        await parliament.stop()
        for agent in mock_agents:
            agent.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliberate_success(self, mock_agents):
        """Test the full deliberate loop with 100% success."""
        parliament = Parliament(sub_agents=mock_agents)

        # Override the speaker's final task separately so we can identify the output
        mock_agents[0].execute_task.side_effect = [
            "Agent 0 Initial",  # Round 1
            '{"strengths": "S", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',  # Round 2
            '{"final_answer": "Final Consensus", "consensus_confidence": 95.0, "reasoning": "R"}',  # Synthesis
        ]

        mock_agents[1].execute_task.side_effect = [
            "Agent 1 Initial",
            '{"strengths": "S", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.8}',
        ]

        mock_agents[2].execute_task.side_effect = [
            "Agent 2 Initial",
            '{"strengths": "S", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.7}',
        ]

        result = await parliament.deliberate("Is AI going to take over?")

        assert isinstance(result, dict)
        assert result["final_answer"] == "Final Consensus"
        assert mock_agents[0].execute_task.call_count == 3
        assert mock_agents[1].execute_task.call_count == 2
        assert mock_agents[2].execute_task.call_count == 2

    @pytest.mark.asyncio
    async def test_deliberate_with_agent_failure(self, mock_agents):
        """Test deliberation continues gracefully if an agent fails an initial answer."""
        parliament = Parliament(sub_agents=mock_agents)

        # Agent 1 fails their initial answer
        mock_agents[1].execute_task.side_effect = [
            Exception("LLM Timeout"),  # Round 1
            '{"strengths": "S", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.5}',
        ]

        mock_agents[0].execute_task.side_effect = [
            "Agent 0 Initial",
            '{"strengths": "S", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
            '{"final_answer": "Final Consensus", "consensus_confidence": 90.0, "reasoning": "R"}',
        ]

        mock_agents[2].execute_task.side_effect = [
            "Agent 2 Initial",
            '{"strengths": "S", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.8}',
        ]

        result = await parliament.deliberate("Hard question")

        assert result["final_answer"] == "Final Consensus"

    def test_deliberate_sync(self, mock_agents):
        """Test the synchronous wrapper execution."""
        parliament = Parliament(sub_agents=mock_agents)

        # When using side_effect with AsyncMock in sync loops, it acts identically.
        mock_agents[0].execute_task.return_value = (
            '{"final_answer": "Test Sync Return", "consensus_confidence": 99.0, "reasoning": "R"}'
        )

        result = parliament.deliberate_sync("Sync test question")
        assert result["final_answer"] == "Test Sync Return"

    @pytest.mark.asyncio
    async def test_deliberate_multiple_rounds(self, mock_agents):
        """Test the deliberate loop with multiple review rounds."""
        parliament = Parliament(sub_agents=mock_agents, max_review_rounds=3)

        # Speaker (agent 0) executes: 1 initial + 3 reviews + 1 synthesis = 5 calls
        mock_agents[0].execute_task.side_effect = [
            "Alpha Initial completely unique wording",
            '{"strengths": "Apple", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
            '{"strengths": "Avocado", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
            '{"strengths": "Apricot", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
            '{"final_answer": "Final Consensus", "consensus_confidence": 95.0, "reasoning": "R"}',
        ]

        # Other agents execute: 1 initial + 3 reviews = 4 calls
        mock_agents[1].execute_task.side_effect = [
            "Beta Initial completely unique wording",
            '{"strengths": "Banana", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.8}',
            '{"strengths": "Blueberry", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.8}',
            '{"strengths": "Blackberry", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.8}',
        ]

        mock_agents[2].execute_task.side_effect = [
            "Gamma Initial completely unique wording",
            '{"strengths": "Cherry", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.7}',
            '{"strengths": "Coconut", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.7}',
            '{"strengths": "Cranberry", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.7}',
        ]

        result = await parliament.deliberate("Iterative question")

        assert result["final_answer"] == "Final Consensus"
        assert mock_agents[0].execute_task.call_count == 5
        assert mock_agents[1].execute_task.call_count == 4
        assert mock_agents[2].execute_task.call_count == 4

    @pytest.mark.asyncio
    async def test_early_stopping(self, mock_agents):
        """Test that deliberation stops early if similarity threshold is met."""
        # Lower threshold for deterministic mock testing
        parliament = Parliament(
            sub_agents=mock_agents, max_review_rounds=3, config={"agreement_threshold": 0.5}
        )

        # We output IDENTICAL strings for reviews to force 1.0 TF-IDF cosine similarity.
        mock_agents[0].execute_task.side_effect = [
            "Agent 0 Initial",
            '{"strengths": "Identical highly similar review string forcing agreement.", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
            '{"final_answer": "Final Consensus", "consensus_confidence": 95.0, "reasoning": "R"}',
        ]

        mock_agents[1].execute_task.side_effect = [
            "Agent 1 Initial",
            '{"strengths": "Identical highly similar review string forcing agreement.", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
        ]

        mock_agents[2].execute_task.side_effect = [
            "Agent 2 Initial",
            '{"strengths": "Identical highly similar review string forcing agreement.", "weaknesses": "W", "suggested_improvements": "I", "confidence": 0.9}',
        ]

        result = await parliament.deliberate("Question mapping early stop")

        assert result["final_answer"] == "Final Consensus"
        # Since it stops early after Round 1, it only does: Initial + Review 1 + Synthesis
        assert mock_agents[0].execute_task.call_count == 3
        assert mock_agents[1].execute_task.call_count == 2
        assert mock_agents[2].execute_task.call_count == 2
