from unittest.mock import AsyncMock, patch

import pytest

from daie.agents import Agent, AgentConfig
from daie.core.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    main = Agent(config=AgentConfig(name="Main"))
    sub1 = Agent(config=AgentConfig(name="Sub1"))
    sub2 = Agent(config=AgentConfig(name="Sub2"))

    orch = Orchestrator(
        main, [sub1, sub2], context_name="TestContext", main_role="Leader", sub_role="Follower"
    )

    assert orch.main_agent == main
    assert len(orch.sub_agents) == 2
    assert orch.context_name == "TestContext"
    assert orch.main_role == "Leader"
    assert orch.sub_role == "Follower"


@pytest.mark.asyncio
async def test_orchestrator_start_configures_prompts():
    judge = Agent(config=AgentConfig(name="Judge"))
    lawyer = Agent(config=AgentConfig(name="Lawyer"))

    court = Orchestrator(
        judge, [lawyer], context_name="Courtroom", main_role="Judge", sub_role="Lawyer"
    )

    # Mock agent starts
    with patch.object(Agent, "start", new_callable=AsyncMock):
        await court.start()

        # Verify prompts were updated with custom roles
        assert "JUDGE" in judge.config.system_prompt
        assert "Courtroom" in judge.config.system_prompt
        assert "LAWYER" in lawyer.config.system_prompt
        assert "Judge" in lawyer.config.system_prompt

        await court.stop()


@pytest.mark.asyncio
async def test_orchestrator_execution():
    main = Agent(config=AgentConfig(name="Main"))
    sub = Agent(config=AgentConfig(name="Sub"))

    orch = Orchestrator(main, [sub])

    # Mock main_agent.execute_task and start
    with patch.object(Agent, "start", new_callable=AsyncMock):
        with patch.object(Agent, "execute_task", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Orchestrated Answer"

            result = await orch.execute_task("Do something")

            assert result == "Orchestrated Answer"
            mock_exec.assert_called_once_with("Do something")

            await orch.stop()
