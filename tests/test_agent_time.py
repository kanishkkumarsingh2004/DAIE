import asyncio
import datetime
from daie import Agent, AgentConfig, AgentRole


async def test_temporal_awareness():
    print("\n--- Testing Agent Temporal Awareness ---")

    # 1. Check default behavior (include_datetime=True)
    config = AgentConfig(name="TimeKeeper", role=AgentRole.GENERAL_PURPOSE, include_datetime=True)
    agent = Agent(config=config)

    # Check internal prompt building
    prompt = agent._build_system_prompt()
    now = datetime.datetime.now()
    year = str(now.year)

    print(f"Checking if '{year}' is in system prompt...")
    if year in prompt:
        print("✅ SUCCESS: Current year found in system prompt.")
    else:
        print("❌ FAILURE: Current year NOT found in system prompt.")
        # print("Prompt snippet:", prompt[:500])

    # Check block title
    if "SYSTEM CONTEXT & TEMPORAL" in prompt:
        print("✅ SUCCESS: Temporal block title found.")
    else:
        print("❌ FAILURE: Temporal block title missing.")

    # 2. Check disabled behavior
    config_disabled = AgentConfig(
        name="NoTime", role=AgentRole.GENERAL_PURPOSE, include_datetime=False
    )
    agent_no_time = Agent(config=config_disabled)
    prompt_no_time = agent_no_time._build_system_prompt()

    if "SYSTEM CONTEXT & TEMPORAL" not in prompt_no_time:
        print("✅ SUCCESS: Temporal block correctly omitted when disabled.")
    else:
        print("❌ FAILURE: Temporal block found even when disabled.")


if __name__ == "__main__":
    asyncio.run(test_temporal_awareness())
