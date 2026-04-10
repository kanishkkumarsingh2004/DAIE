"""
Tests for the Parliament mixture-of-agents architecture.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
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
            {"agent_id": 2, "answer": "Water is wet"}
        ]
        
        review_prompt = parliament._build_review_prompt("What are facts?", other_answers)
        
        assert "What are facts?" in review_prompt
        assert "Agent 1 answer:\nThe sky is blue" in review_prompt
        assert "Agent 2 answer:\nWater is wet" in review_prompt
        assert "Do NOT review yourself" in review_prompt

    def test_build_synthesis_prompt(self, mock_agents):
        """Test that the synthesis prompt correctly bundles answers and reviews."""
        parliament = Parliament(sub_agents=mock_agents)
        
        initial_answers = [
            {"agent_id": 0, "answer": "A"},
            {"agent_id": 1, "answer": "B"}
        ]
        
        reviews = [
            "A is correct",  # Review from Agent 0
            Exception("Simulated Failure")  # Failed review from Agent 1
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
            "Agent 0 Review",   # Round 2
            "Final Consensus"   # Synthesis
        ]
        
        mock_agents[1].execute_task.side_effect = [
            "Agent 1 Initial",
            "Agent 1 Review"
        ]
        
        mock_agents[2].execute_task.side_effect = [
            "Agent 2 Initial",
            "Agent 2 Review"
        ]
        
        result = await parliament.deliberate("Is AI going to take over?")
        
        assert result == "Final Consensus"
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
            "Agent 1 Review"           # Round 2 (assuming they still review)
        ]
        
        mock_agents[0].execute_task.side_effect = [
            "Agent 0 Initial",
            "Agent 0 Review",
            "Final Consensus"
        ]
        
        mock_agents[2].execute_task.side_effect = [
            "Agent 2 Initial",
            "Agent 2 Review"
        ]
        
        result = await parliament.deliberate("Hard question")
        
        assert result == "Final Consensus"

    def test_deliberate_sync(self, mock_agents):
        """Test the synchronous wrapper execution."""
        parliament = Parliament(sub_agents=mock_agents)
        
        # When using side_effect with AsyncMock in sync loops, it acts identically.
        mock_agents[0].execute_task.return_value = "Test Sync Return"
        
        result = parliament.deliberate_sync("Sync test question")
        assert result == "Test Sync Return"
