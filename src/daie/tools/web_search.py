"""
Web Search Tool — DuckDuckGo with Tavily fallback.

Provides web search capabilities for agents using DuckDuckGo (no API key)
with an optional Tavily fallback when TAVILY_API_KEY is set.
"""

import logging
import os
from typing import Any, Dict, List

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)


class WebSearchTool(Tool):
    """
    Web search tool using DuckDuckGo (free, no API key required).

    Falls back to Tavily if ``TAVILY_API_KEY`` environment variable is set.

    Example:
        >>> tool = WebSearchTool()
        >>> result = await tool.execute({"query": "Python AI frameworks"})
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="web_search",
            description="Search the web for information. Returns titles, URLs, and snippets.",
            category=ToolCategory.SEARCH,
            version="1.0.0",
            author="DAIE",
            capabilities=["web_search", "information_retrieval"],
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query text",
                    required=True,
                ),
                ToolParameter(
                    name="num_results",
                    type="integer",
                    description="Number of results to return (default: 5)",
                    required=False,
                    default=5,
                ),
                ToolParameter(
                    name="region",
                    type="string",
                    description="Region code for localized results (e.g., 'us-en', 'uk-en')",
                    required=False,
                    default=None,
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Any:
        query = params["query"]
        num_results = params.get("num_results", 5)
        region = params.get("region")

        # Try Tavily first if API key is available
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            try:
                return await self._search_tavily(query, num_results, tavily_key)
            except Exception as e:
                logger.warning(f"Tavily search failed, falling back to DuckDuckGo: {e}")

        # DuckDuckGo (default)
        return await self._search_duckduckgo(query, num_results, region)

    async def _search_duckduckgo(
        self, query: str, num_results: int, region: str = None
    ) -> Dict[str, Any]:
        """Search using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError(
                "duckduckgo-search not installed. "
                "Install with: pip install duckduckgo-search"
            )

        import asyncio

        def _search():
            with DDGS() as ddgs:
                kwargs = {"keywords": query, "max_results": num_results}
                if region:
                    kwargs["region"] = region
                results = list(ddgs.text(**kwargs))
                return results

        raw_results = await asyncio.to_thread(_search)

        formatted = []
        for r in raw_results:
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("href", r.get("link", "")),
                "snippet": r.get("body", r.get("snippet", "")),
            })

        return {
            "query": query,
            "provider": "duckduckgo",
            "num_results": len(formatted),
            "results": formatted,
        }

    async def _search_tavily(
        self, query: str, num_results: int, api_key: str
    ) -> Dict[str, Any]:
        """Search using Tavily API."""
        import asyncio
        import json
        import urllib.request

        def _search():
            url = "https://api.tavily.com/search"
            payload = json.dumps({
                "api_key": api_key,
                "query": query,
                "max_results": num_results,
                "search_depth": "basic",
            }).encode("utf-8")

            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            return data

        data = await asyncio.to_thread(_search)

        formatted = []
        for r in data.get("results", []):
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            })

        return {
            "query": query,
            "provider": "tavily",
            "num_results": len(formatted),
            "results": formatted,
        }
