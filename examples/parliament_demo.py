"""
Parliament Deliberation Demo.

Demonstrates the 'Mixture-of-Agents' peer-review architecture.
Four agents acting out distinct specialized roles answer a deep philosophical question,
peer-review each other's answers, and synthesize the result.
"""

from daie import Agent, AgentConfig, AgentRole
from daie.agents import Parliament

# Ensure the mock or real LLM is set
from daie.core import set_llm
set_llm(ollama_llm="llama3.2")

# Initialize four agents with different perspectives
# Setting temperature lower prevents total creative hallucination during facts
economist_config = AgentConfig(name="Economist", role=AgentRole.DATA_ANALYST, system_prompt="You are an Economist.", temperature=0.3)
lawyer_config = AgentConfig(name="Lawyer", role=AgentRole.SECURITY_AUDITOR, system_prompt="You are a Lawyer.", temperature=0.3)
scientist_config = AgentConfig(name="Scientist", role=AgentRole.RESEARCHER, system_prompt="You are a Scientist.", temperature=0.3)
ethicist_config = AgentConfig(name="Ethicist", role=AgentRole.GENERAL_PURPOSE, system_prompt="You are an Ethicist.", temperature=0.5)

agents = [
    Agent(config=economist_config),
    Agent(config=lawyer_config),
    Agent(config=scientist_config),
    Agent(config=ethicist_config)
]

# Create the Parliament instance.
# The speaker (synthesizer) defaults to the first agent (Economist) if omitted, 
# but setting an explicit speaker is useful conceptually.
parliament = Parliament(sub_agents=agents, speaker=agents[0])

from daie.chat import ParliamentChatConfig

# Start the interactive chat loop!
config = ParliamentChatConfig(parliament=parliament)

print("\n🚀 Parliament successfully assembled!")
print("Here are some debate topics you could try entering:")
print(" - 'Should a highly developed but resource-constrained nation adopt Universal Basic Income?'")
print(" - 'Is the deployment of autonomous weapons ethical if they mathematically reduce civilian casualties?'")
print(" - 'Should artificial intelligence research be paused immediately?'\n")

# Launches the interactive loop (auto-starts sub-agents under the hood)
config.run()
