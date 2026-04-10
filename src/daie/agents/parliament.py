"""
Parliament Architecture for peer-reviewed agent deliberation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from daie.agents.agent import Agent

logger = logging.getLogger(__name__)


class Parliament:
    """
    Parliament Architecture for deliberative consensus.
    - All sub-agents receive the exact same prompt and answer it.
    - Each agent reviews ALL other answers (no self-review).
    - A final synthesis produces the definitive output.
    """

    def __init__(
        self,
        sub_agents: List[Agent],
        speaker: Optional[Agent] = None,
        max_review_rounds: int = 1,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a Parliament of agents.
        
        Args:
            sub_agents: A list of DAIE Agents to form the parliament.
            speaker: An optional Agent to act as the synthesizer. Defaults to the first sub_agent.
            max_review_rounds: Number of review rounds before synthesis.
            config: Additional configuration parameters.
        """
        if len(sub_agents) < 2:
            raise ValueError("Parliament needs at least 2 agents for peer review.")
        
        self.sub_agents = sub_agents
        self.speaker = speaker or sub_agents[0]
        self.max_review_rounds = max_review_rounds
        self.config = config or {}

    async def start(self) -> None:
        """Start all sub-agents in the parliament."""
        logger.info(f"Starting Parliament with {len(self.sub_agents)} members...")
        starts = [agent.start() for agent in self.sub_agents]
        await asyncio.gather(*starts, return_exceptions=True)
        
    async def stop(self) -> None:
        """Stop all sub-agents in the parliament."""
        logger.info("Adjourning Parliament...")
        stops = [agent.stop() for agent in self.sub_agents]
        await asyncio.gather(*stops, return_exceptions=True)

    async def deliberate(self, prompt: str) -> str:
        """
        Main method stringing together initial prompts, peer-review, and final synthesis.
        
        Args:
            prompt: The question or task to deliberate on.
            
        Returns:
            The synthesized consensus answer.
        """
        logger.info(f"Parliament deliberation started with {len(self.sub_agents)} agents.")

        # === ROUND 1: All agents answer the same prompt (parallel) ===
        initial_answers = await asyncio.gather(
            *[agent.execute_task(prompt) for agent in self.sub_agents],
            return_exceptions=True
        )

        # Handle any failures gracefully
        answers = []
        for i, result in enumerate(initial_answers):
            if isinstance(result, Exception):
                logger.warning(f"Agent {i} failed initial answer: {result}")
                answers.append(f"[Agent {i} failed to answer]")
            else:
                answers.append(str(result))

        # Store answers with agent index for easy reference
        agent_answers = [
            {"agent_id": i, "answer": ans}
            for i, ans in enumerate(answers)
        ]

        # === ROUND 2: Peer Review (no self-review) ===
        review_tasks = []
        for i, reviewer in enumerate(self.sub_agents):
            others = [a for j, a in enumerate(agent_answers) if j != i]
            
            review_prompt = self._build_review_prompt(prompt, others)
            review_tasks.append(reviewer.execute_task(review_prompt))

        reviews = await asyncio.gather(*review_tasks, return_exceptions=True)

        # === FINAL SYNTHESIS ===
        final_prompt = self._build_synthesis_prompt(prompt, agent_answers, reviews)
        final_output = await self.speaker.execute_task(final_prompt)

        logger.info("Parliament deliberation completed.")
        return final_output

    def _build_review_prompt(self, original_prompt: str, other_answers: List[Dict[str, Any]]) -> str:
        """Builds the review prompt for one agent."""
        review_text = "\n\n".join(
            f"Agent {ans['agent_id']} answer:\n{ans['answer']}"
            for ans in other_answers
        )
        return f"""You are reviewing answers from other parliament members.

Original question: {original_prompt}

Here are the other agents' answers:
{review_text}

Critically analyze them. Point out strengths, weaknesses, factual errors, and biases.
Be constructive and objective. Do NOT review yourself."""

    def _build_synthesis_prompt(
        self,
        original_prompt: str,
        initial_answers: List[Dict[str, Any]],
        reviews: List[Any]
    ) -> str:
        """Builds the final synthesis prompt for the Speaker."""
        review_text = "\n\n".join(
            f"Review from Agent {i}: {str(r) if not isinstance(r, Exception) else '[Review failed]'}"
            for i, r in enumerate(reviews)
        )

        initial_text = "\n".join(f"Agent {a['agent_id']}: {a['answer']}" for a in initial_answers)

        return f"""You are the Speaker of the Parliament.
All agents have answered the same question and reviewed each other.

Question: {original_prompt}

Initial answers:
{initial_text}

Peer reviews:
{review_text}

Synthesize everything into ONE clear, accurate, and comprehensive final answer.
Resolve contradictions. Remove hallucinations. Keep only what survived peer review.
Be concise but complete."""

    def deliberate_sync(self, prompt: str) -> str:
        """
        Synchronous wrapper for the deliberate method.
        """
        return asyncio.run(self.deliberate(prompt))
