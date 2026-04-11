from __future__ import annotations
from typing import List, Any, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    DAIE Parallel Execution Layer
    Runs independent agent tasks concurrently without waiting.
    """

    def __init__(self, max_concurrency: int = 8):
        """
        max_concurrency: limits simultaneous agent executions
        (useful for local LLMs like Ollama to avoid OOM or slowdown)
        """
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def run_parallel(
        self,
        tasks: List[Awaitable[Any]],
        return_exceptions: bool = True,
    ) -> List[Any]:
        """
        Run multiple async tasks (e.g. agent.execute_task) in parallel.
        """
        if not tasks:
            return []

        async def _safe_run(task: Awaitable[Any]) -> Any:
            async with self.semaphore:
                try:
                    return await task
                except Exception as e:
                    logger.warning(f"Parallel task failed: {e}")
                    if return_exceptions:
                        return e
                    raise

        logger.info(
            f"Running {len(tasks)} tasks in parallel (max_concurrency={self.max_concurrency})"
        )

        results = await asyncio.gather(
            *[_safe_run(task) for task in tasks], return_exceptions=return_exceptions
        )

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Parallel execution completed: {success_count}/{len(tasks)} successful")
        return results

    # Convenience method for agents
    async def run_agents(
        self,
        agents: List["Agent"],  # type: ignore - forward ref # noqa: F821
        method_name: str,
        *args,
        **kwargs,
    ) -> List[Any]:
        """Run the same method on multiple agents in parallel (e.g. execute_task)"""
        coros = [getattr(agent, method_name)(*args, **kwargs) for agent in agents]
        return await self.run_parallel(coros)
