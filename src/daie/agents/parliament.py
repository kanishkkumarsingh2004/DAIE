"""
Parliament Architecture for peer-reviewed agent deliberation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from daie.agents.agent import Agent
from daie.agents.message import AgentMessage
from daie.agents.router import AgentRouter
from daie.core.parallel_executor import ParallelExecutor

logger = logging.getLogger(__name__)


# --- Pydantic Models for Structured Output ---
class ReviewOutput(BaseModel):
    strengths: str = Field(description="Strengths of the previous answers")
    weaknesses: str = Field(description="Weaknesses and flaws of the previous answers")
    suggested_improvements: str = Field(description="Actionable improvements to fix flaws")
    confidence: float = Field(description="Confidence weight of this review block from 0.0 to 1.0")


class ConsensusOutput(BaseModel):
    final_answer: str = Field(description="The finalized, synthesized, fully complete answer")
    consensus_confidence: float = Field(
        description="Aggregate holistic confidence metric from 0.0 to 100.0 (percentage)"
    )
    reasoning: str = Field(
        description="Brief reasoning on how consensus was reached and contradictions were resolved"
    )


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
        config: Optional[Dict[str, Any]] = None,
        max_concurrency: int = 8,
        distributed: bool = False,
        communication_manager: Optional[Any] = None,
        distributed_timeout: int = 30,
    ):
        """
        Initialize a Parliament of agents.

        Args:
            sub_agents: A list of DAIE Agents to form the parliament.
            speaker: An optional Agent to act as the synthesizer. Defaults to the first sub_agent.
            max_review_rounds: Number of review rounds before synthesis.
            config: Additional configuration parameters.
            max_concurrency: Concurrency limit for local execution.
            distributed: If True, uses CommunicationManager to DELIVER tasks to remote nodes.
            communication_manager: The CommunicationManager to use for distributed tasks.
            distributed_timeout: Seconds to wait for remote responses.
        """
        if not distributed and len(sub_agents) < 2:
            raise ValueError("Parliament needs at least 2 agents for peer review.")

        self.sub_agents = sub_agents
        self.speaker = speaker or sub_agents[0]
        self.max_review_rounds = max_review_rounds
        self.config = config or {}
        self.parallel_executor = ParallelExecutor(max_concurrency=max_concurrency)
        self.router: Optional[AgentRouter] = None
        self.distributed = distributed
        self.communication_manager = communication_manager
        self.distributed_timeout = distributed_timeout
        self._parliament_id = f"parliament_{id(self)}"

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

        # === ROUND 1: All agents answer the same prompt ===
        if self.distributed:
            answers = await self._deliberate_distributed(prompt, [a.id for a in self.sub_agents])
        else:
            initial_tasks = [agent.execute_task(prompt) for agent in self.sub_agents]
            initial_answers = await self.parallel_executor.run_parallel(
                initial_tasks, return_exceptions=True
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
        agent_answers = [{"agent_id": i, "answer": ans} for i, ans in enumerate(answers)]

        # === MULTIPLE PEER REVIEW ROUNDS ===
        current_answers = agent_answers
        reviews = []  # Will store the final round output

        for round_idx in range(1, self.max_review_rounds + 1):
            logger.info(f"Parliament starting review round {round_idx}/{self.max_review_rounds}")
            if self.distributed:
                # Prepare remote review prompts
                review_prompts = []
                for i, reviewer in enumerate(self.sub_agents):
                    others = [a for j, a in enumerate(current_answers) if j != i]
                    review_prompt = self._build_review_prompt(prompt, others, round_num=round_idx)
                    review_prompts.append((reviewer.id, review_prompt))

                # Execute in parallel over P2P
                round_results = await self._deliberate_distributed_multi(review_prompts)
            else:
                review_tasks = []
                for i, reviewer in enumerate(self.sub_agents):
                    others = [a for j, a in enumerate(current_answers) if j != i]
                    review_prompt = self._build_review_prompt(prompt, others, round_num=round_idx)
                    review_tasks.append(reviewer.execute_task(review_prompt))

                round_results = await self.parallel_executor.run_parallel(
                    review_tasks, return_exceptions=True
                )

            # Format answers safely by parsing JSON returns
            parsed_reviews = []
            for i, r in enumerate(round_results):
                if isinstance(r, Exception):
                    parsed_reviews.append(f"[Agent {i} failed]")
                    continue
                try:
                    raw_dict = Agent._parse_llm_json(str(r))
                    if raw_dict:
                        model = ReviewOutput(**raw_dict)
                        # We represent the review block back as a json string for the next prompt iteration
                        parsed_reviews.append(model.model_dump_json(indent=2))
                    else:
                        parsed_reviews.append(f"[Agent {i} failed structured validation]")
                except ValidationError:
                    parsed_reviews.append(f"[Agent {i} failed structured validation]")
            reviews = parsed_reviews

            # EARLY STOPPING CHECK
            agreement = self._calculate_agreement(reviews)
            agreement_threshold = self.config.get(
                "agreement_threshold", 0.85
            )  # 85% overlap defaults
            if agreement >= agreement_threshold:
                logger.info(
                    f"Parliament reached early consensus (similarity: {agreement:.2f} >= {agreement_threshold}). Stopping early."
                )
                break

            current_answers = [{"agent_id": i, "answer": rev} for i, rev in enumerate(reviews)]

        # === FINAL SYNTHESIS ===
        final_prompt = self._build_synthesis_prompt(prompt, agent_answers, reviews)
        raw_final_output = await self.speaker.execute_task(final_prompt)

        # Parse final output securely
        final_dict = Agent._parse_llm_json(str(raw_final_output))
        if final_dict:
            try:
                final_consensus = ConsensusOutput(**final_dict).model_dump()
            except ValidationError:
                final_consensus = {
                    "final_answer": str(raw_final_output),
                    "consensus_confidence": 0.0,
                    "reasoning": "Fallback response.",
                }
        else:
            final_consensus = {
                "final_answer": str(raw_final_output),
                "consensus_confidence": 0.0,
                "reasoning": "Fallback response.",
            }

        logger.info("Parliament deliberation completed.")
        return final_consensus

    async def deliberate_with_router(
        self, prompt: str, all_agents: List[Agent], top_k: int = 6
    ) -> Dict[str, Any]:
        """
        Dynamically selects the best top_k agents from all_agents pool using the DAIE AgentRouter,
        and proceeds with a standard deliberation loop using only that specialized subset.
        """
        logger.info(
            f"Dynamically selecting top {top_k} agents via AgentRouter for parliament deliberation."
        )
        if self.router is None:
            self.router = AgentRouter.from_agents(all_agents)

        selected = await self.router.select_agents(prompt, all_agents, top_k)

        # Override structural assignments
        self.sub_agents = selected
        if self.speaker not in self.sub_agents:
            self.speaker = self.sub_agents[0]

        return await self.deliberate(prompt)

    async def _deliberate_distributed(self, prompt: str, target_ids: List[str]) -> List[str]:
        """Broadcasts a prompt to multiple remote agent IDs and waits for results."""
        if not self.communication_manager:
            raise ValueError("CommunicationManager required for distributed parliament.")

        results = {tid: f"[Agent {tid} failed to answer]" for tid in target_ids}
        received_count = 0
        completion_event = asyncio.Event()

        async def response_handler(msg: AgentMessage):
            nonlocal received_count
            corr_id = msg.metadata.get("correlation_id")
            if corr_id == self._parliament_id:
                if not target_ids or msg.sender_id in results:
                    results[msg.sender_id] = msg.content
                    received_count += 1
                    if target_ids and received_count >= len(target_ids):
                        completion_event.set()

        # Register temp handler for responses directed to this parliament pseudo-agent
        self.communication_manager.register_agent_handler(self._parliament_id, response_handler)

        try:
            # Send tasks
            if not target_ids:
                # No specific IDs, broadcast to all nodes in the ecosystem
                msg = AgentMessage(
                    sender_id=self._parliament_id,
                    receiver_id="*",
                    content=prompt,
                    message_type="parliament_deliberate",
                    metadata={"correlation_id": self._parliament_id},
                )
                await self.communication_manager.broadcast_message(msg)
            else:
                # Targeted tasks to known remote agents
                for tid in target_ids:
                    msg = AgentMessage(
                        sender_id=self._parliament_id,
                        receiver_id=tid,
                        content=prompt,
                        message_type="task",
                        metadata={"correlation_id": self._parliament_id},
                    )
                    await self.communication_manager.send_message(msg)

            # Wait for completion or timeout
            try:
                await asyncio.wait_for(completion_event.wait(), timeout=self.distributed_timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Distributed parliament timed out after {self.distributed_timeout}s."
                )

            return [results[tid] for tid in target_ids]
        finally:
            self.communication_manager.unregister_agent_handler(self._parliament_id)

    async def _deliberate_distributed_multi(
        self, target_prompts: List[tuple[str, str]]
    ) -> List[str]:
        """Sends different prompts to multiple remote agent IDs and waits for results."""
        if not self.communication_manager:
            raise ValueError("CommunicationManager required for distributed parliament.")

        target_ids = [tp[0] for tp in target_prompts]
        results = {tid: f"[Agent {tid} failed]" for tid in target_ids}
        received_count = 0
        completion_event = asyncio.Event()

        async def response_handler(msg: AgentMessage):
            nonlocal received_count
            corr_id = msg.metadata.get("correlation_id")
            if corr_id == self._parliament_id and msg.sender_id in results:
                results[msg.sender_id] = msg.content
                received_count += 1
                if received_count >= len(target_ids):
                    completion_event.set()

        # Register temp handler
        self.communication_manager.register_agent_handler(self._parliament_id, response_handler)

        try:
            for tid, prompt in target_prompts:
                msg = AgentMessage(
                    sender_id=self._parliament_id,
                    receiver_id=tid,
                    content=prompt,
                    message_type="task",
                    metadata={"correlation_id": self._parliament_id},
                )
                await self.communication_manager.send_message(msg)

            try:
                await asyncio.wait_for(completion_event.wait(), timeout=self.distributed_timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Distributed parliament timed out after {self.distributed_timeout}s."
                )

            return [results[tid] for tid in target_ids]
        finally:
            self.communication_manager.unregister_agent_handler(self._parliament_id)

    def _calculate_agreement(self, reviews: List[str]) -> float:
        """Calculate TF-IDF embedding cosine similarity between reviews."""
        valid_reviews = [str(r) for r in reviews if not str(r).startswith("[Agent ")]
        if len(valid_reviews) < 2:
            return 0.0

        try:
            from daie.rag.backends import TFIDFBackend
            from daie.rag.chunking import Chunk
            import numpy as np

            backend = TFIDFBackend()
            chunks = [
                Chunk(text=r, source="review", chunk_index=i) for i, r in enumerate(valid_reviews)
            ]
            backend.index(chunks)
            matrix = backend._tfidf_matrix

            if matrix is None or matrix.shape[1] == 0:
                return 0.0

            # Compute pairwise cosine similarity
            norms = np.linalg.norm(matrix, axis=1)
            norms = np.where(norms == 0, 1.0, norms)
            norm_matrix = matrix / norms[:, np.newaxis]

            sim_matrix = np.dot(norm_matrix, norm_matrix.T)

            # Average off-diagonal elements
            n = len(valid_reviews)
            mask = ~np.eye(n, dtype=bool)
            avg_sim = float(np.mean(sim_matrix[mask]))
            return avg_sim

        except Exception as e:
            logger.warning(f"Failed to calculate TF-IDF agreement: {e}")
            return 0.0

    def _build_review_prompt(
        self, original_prompt: str, other_answers: List[Dict[str, Any]], round_num: int = 1
    ) -> str:
        """Builds the review prompt for one agent."""
        context_type = "answer" if round_num == 1 else "latest review/update"
        review_text = "\n\n".join(
            f"Agent {ans['agent_id']} {context_type}:\n{ans['answer']}" for ans in other_answers
        )
        return f"""You are participating in review round {round_num} of parliamentary deliberation.

Original question: {original_prompt}

Here are the other agents' responses from the previous round:
{review_text}

Critically analyze them. Point out strengths, weaknesses, factual errors, and biases.
Be constructive and objective. Provide your updated perspective. Do NOT review yourself.

You MUST respond strictly in RAW JSON format matching exactly this schema, and nothing else (no markdown):
{{
  "strengths": "String detailing strengths",
  "weaknesses": "String detailing weaknesses",
  "suggested_improvements": "String detailing improvements",
  "confidence": 0.95
}}"""

    def _build_synthesis_prompt(
        self, original_prompt: str, initial_answers: List[Dict[str, Any]], reviews: List[Any]
    ) -> str:
        """Builds the final synthesis prompt for the Speaker."""
        review_text = "\n\n".join(
            f"Review from Agent {i}: {str(r) if not isinstance(r, Exception) else '[Review failed]'}"
            for i, r in enumerate(reviews)
        )

        initial_text = "\n".join(f"Agent {a['agent_id']}: {a['answer']}" for a in initial_answers)

        return f"""You are the Speaker of the Parliament.
All agents have answered the same question and reviewed each other iteratively.

Question: {original_prompt}

Initial answers:
{initial_text}

Peer reviews (last generation block):
{review_text}

Synthesize everything into ONE clear, accurate, and comprehensive final answer to the original question.
Resolve contradictions. Remove hallucinations. Keep only what survived peer review.
Weight the outcomes significantly using the highest confidence variables provided in the peer reviews.

CRITICAL INSTRUCTION: The user ONLY wants the final, synthesized answer. DO NOT mention the Parliament, the review process, or what any specific Agent said. Do not say "Agent 0 said...". Just answer the question directly as a single, unified intelligence.

You MUST respond strictly in RAW JSON format matching exactly this schema, and nothing else (no markdown):
{{
  "final_answer": "String of final synthesized answer",
  "consensus_confidence": 92.5,
  "reasoning": "String abstracting how differences were resolved"
}}"""

    def deliberate_sync(self, prompt: str) -> str:
        """
        Synchronous wrapper for the deliberate method.
        """
        return asyncio.run(self.deliberate(prompt))
