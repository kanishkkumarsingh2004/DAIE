import logging
import os
import json
import asyncio
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)

# Common User-Agents to prevent blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


class WebSearchTool(Tool):
    """
    High-value Web Search tool using DuckDuckGo with Tavily fallback.

    Provides robust web searching with native async execution patterns.
    - DuckDuckGo: Default, no API key required.
    - Tavily: Fallback or primary if TAVILY_API_KEY is present.

    Example:
        >>> tool = WebSearchTool()
        >>> result = await tool.execute({"query": "Latest breakthroughs in fusion energy"})
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="web_search",
            description="Perform a web search to find latest information, news, and technical data.",
            category=ToolCategory.SEARCH,
            version="1.1.0",
            author="DAIE",
            capabilities=["web_search", "information_retrieval", "news_lookup"],
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search query to perform",
                    required=True,
                ),
                ToolParameter(
                    name="num_results",
                    type="integer",
                    description="Maximum number of results to return (default: 5, max: 20)",
                    required=False,
                    default=5,
                ),
                ToolParameter(
                    name="search_depth",
                    type="string",
                    description="Search depth: 'basic' or 'advanced' (mostly for Tavily)",
                    choices=["basic", "advanced"],
                    required=False,
                    default="basic",
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Any:
        query = params["query"]
        num_results = min(params.get("num_results", 5), 20)
        search_depth = params.get("search_depth", "basic")

        # Prioritize Tavily if API key is present for higher quality
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            try:
                return await self._search_tavily(query, num_results, search_depth, tavily_key)
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")

        # Default to DuckDuckGo
        return await self._search_duckduckgo(query, num_results)

    async def _search_duckduckgo(self, query: str, num_results: int) -> Dict[str, Any]:
        """Async-wrapped DuckDuckGo search."""
        try:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                from ddgs import DDGS
        except ImportError:
            raise ImportError("duckduckgo-search not installed. Run: pip install duckduckgo-search")

        def _sync_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=num_results))

        try:
            raw_results = await asyncio.to_thread(_sync_search)
            results = []
            for r in raw_results:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("link", "")),
                        "snippet": r.get("body", r.get("snippet", "")),
                        "source": "duckduckgo",
                    }
                )

            return {"success": True, "query": query, "results": results, "provider": "duckduckgo"}
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {"success": False, "error": str(e), "provider": "duckduckgo"}

    async def _search_tavily(
        self, query: str, num_results: int, depth: str, api_key: str
    ) -> Dict[str, Any]:
        """Native async (via to_thread) Tavily API search."""
        import urllib.request
        import random

        def _sync_post():
            url = "https://api.tavily.com/search"
            payload = json.dumps(
                {
                    "api_key": api_key,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": depth,
                    "include_answer": True,
                }
            ).encode("utf-8")

            headers = {"Content-Type": "application/json", "User-Agent": random.choice(USER_AGENTS)}

            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())

        try:
            data = await asyncio.to_thread(_sync_post)
            results = []
            for r in data.get("results", []):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "score": r.get("score", 0.0),
                        "source": "tavily",
                    }
                )

            return {
                "success": True,
                "query": query,
                "results": results,
                "answer": data.get("answer"),
                "provider": "tavily",
            }
        except Exception as e:
            logger.error(f"Tavily API error: {e}")
            raise e
