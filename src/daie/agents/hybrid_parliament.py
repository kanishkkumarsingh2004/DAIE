"""
Hybrid Parliament Orchestrator Pipeline.

Bridges the complex deliberative consensus generation of the `Parliament` assembly
with the concrete execution and task delegation nodes of the `OrchestratorAgent`.
"""

import logging

from daie.agents.parliament import Parliament
from daie.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)


class HybridParliamentOrchestrator:
    """
    Coordinates a multi-agent roadmap debate mapped natively into an actionable
    delegating orchestrator.
    """

    def __init__(
        self,
        parliament: Parliament,
        orchestrator: OrchestratorAgent,
        min_confidence_threshold: float = 60.0,
    ):
        """
        Args:
            parliament: Configured Parliament assembly to act as the strategic planner.
            orchestrator: Orchestrator node configured to decompose and delegate tasks.
            min_confidence_threshold: The minimum percentage `consensus_confidence`
                required from the Parliament speaker to allow the Orchestrator to begin
                delegation. Default is 60.0%.
        """
        self.parliament = parliament
        self.orchestrator = orchestrator
        self.min_confidence_threshold = min_confidence_threshold

    async def execute(self, prompt: str) -> str:
        """
        Executes the hybrid pipeline sequentially.

        Step 1: Assembly deliberates deeply to outline a task-execution roadmap.
        Step 2: Orchestrator absorbs the roadmap and actively delegates workloads.
        """
        logger.info(f"HybridPipeline initiating strategic planning for: {prompt[:50]}...")

        # Phase 1: Strategic Planning via Parliament Consensus
        planning_prompt = (
            f"STRATEGIC PLANNING REQUIRED:\n\n{prompt}\n\n"
            "Debate the necessary strategic steps to fulfill this abstract request. "
            "Resolve any logical contradictions and define a definitive step-by-step roadmap."
        )

        consensus_dict = await self.parliament.deliberate(planning_prompt)

        if not isinstance(consensus_dict, dict):
            return f"Error: Parliament assembly failed to return a structured consensus dictionary. Returned: {consensus_dict}"

        final_roadmap = consensus_dict.get("final_answer", "")
        confidence = consensus_dict.get("consensus_confidence", 0.0)

        if confidence < self.min_confidence_threshold:
            logger.warning(
                f"HybridPipeline halting: Parliament consensus confidence ({confidence}%) falls below safety threshold ({self.min_confidence_threshold}%)."
            )
            return f"Hybrid Pipeline execution aborted: The collective assembly failed to reach a confident resolution. Resolving confidence was only {confidence}%%."

        logger.info(
            f"HybridPipeline Parliament roadmap finalized firmly (Confidence: {confidence}%). Transferring to Orchestrator delegation phase."
        )

        # Phase 2: Active Task Delegation & Execution
        execution_prompt = (
            f"Original Request Protocol: {prompt}\n\n"
            f"Approved Parliament Consensus Roadmap:\n{final_roadmap}\n\n"
            "Execute this roadmap accurately by decomposing the sub-tasks appropriately and deploying your network of specialized agents."
        )

        final_orchestrator_result = await self.orchestrator.decompose_and_execute(execution_prompt)
        logger.info("HybridPipeline orchestration execution successfully terminated.")

        return final_orchestrator_result
