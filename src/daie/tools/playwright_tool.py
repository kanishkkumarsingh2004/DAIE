"""
Playwright Browser Automation Tool.

Modern browser automation using Playwright (async API).
Supports navigation, clicking, typing, screenshots, and JS evaluation.
"""

import logging
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)


class PlaywrightTool(Tool):
    """
    Browser automation tool using Playwright.

    Supports headless/headed Chrome, with operations like navigate,
    click, type, screenshot, get_text, evaluate_js, wait_for_selector.

    Example:
        >>> tool = PlaywrightTool()
        >>> result = await tool.execute({"action": "navigate", "url": "https://example.com"})
        >>> result = await tool.execute({"action": "get_text", "selector": "h1"})
    """

    def __init__(self, headless: bool = True):
        self._headless = headless
        self._browser = None
        self._page = None
        self._playwright = None

        metadata = ToolMetadata(
            name="playwright",
            description="Browser automation using Playwright. Navigate, click, type, screenshot, extract text, run JS.",
            category=ToolCategory.BROWSER_AUTOMATION,
            version="1.0.0",
            author="DAIE",
            capabilities=["browser_automation", "web_scraping", "screenshot"],
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform",
                    required=True,
                    choices=[
                        "navigate", "click", "type", "screenshot",
                        "get_text", "get_html", "evaluate_js",
                        "wait_for_selector", "go_back", "go_forward",
                        "close",
                    ],
                ),
                ToolParameter(
                    name="url",
                    type="string",
                    description="URL to navigate to (for 'navigate' action)",
                    required=False,
                ),
                ToolParameter(
                    name="selector",
                    type="string",
                    description="CSS selector for element operations",
                    required=False,
                ),
                ToolParameter(
                    name="text",
                    type="string",
                    description="Text to type (for 'type' action)",
                    required=False,
                ),
                ToolParameter(
                    name="js_code",
                    type="string",
                    description="JavaScript code to evaluate (for 'evaluate_js' action)",
                    required=False,
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="File path for screenshot (for 'screenshot' action)",
                    required=False,
                    default="screenshot.png",
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Timeout in milliseconds (default: 10000)",
                    required=False,
                    default=10000,
                ),
            ],
        )
        super().__init__(metadata)

    async def _ensure_browser(self):
        """Lazily initialize browser on first use."""
        if self._page is not None:
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Install with: pip install playwright && playwright install chromium"
            )

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._page = await self._browser.new_page()
        logger.info("Playwright browser initialized")

    async def _execute(self, params: Dict[str, Any]) -> Any:
        action = params["action"]
        timeout = params.get("timeout", 10000)

        if action == "close":
            return await self._close()

        await self._ensure_browser()

        if action == "navigate":
            url = params.get("url")
            if not url:
                return {"success": False, "error": "URL is required for navigate action"}
            await self._page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            return {
                "success": True,
                "title": await self._page.title(),
                "url": self._page.url,
            }

        elif action == "click":
            selector = params.get("selector")
            if not selector:
                return {"success": False, "error": "Selector is required for click action"}
            await self._page.click(selector, timeout=timeout)
            return {"success": True, "action": "click", "selector": selector}

        elif action == "type":
            selector = params.get("selector")
            text = params.get("text", "")
            if not selector:
                return {"success": False, "error": "Selector is required for type action"}
            await self._page.fill(selector, text, timeout=timeout)
            return {"success": True, "action": "type", "selector": selector}

        elif action == "screenshot":
            path = params.get("path", "screenshot.png")
            await self._page.screenshot(path=path, full_page=True)
            return {"success": True, "path": path}

        elif action == "get_text":
            selector = params.get("selector")
            if selector:
                element = await self._page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    return {"success": True, "text": text.strip() if text else ""}
                return {"success": False, "error": f"Element not found: {selector}"}
            else:
                text = await self._page.text_content("body")
                return {"success": True, "text": text[:5000] if text else ""}

        elif action == "get_html":
            selector = params.get("selector", "body")
            html = await self._page.inner_html(selector)
            return {"success": True, "html": html[:10000]}

        elif action == "evaluate_js":
            js_code = params.get("js_code")
            if not js_code:
                return {"success": False, "error": "js_code is required for evaluate_js action"}
            result = await self._page.evaluate(js_code)
            return {"success": True, "result": str(result)}

        elif action == "wait_for_selector":
            selector = params.get("selector")
            if not selector:
                return {"success": False, "error": "Selector is required for wait_for_selector"}
            await self._page.wait_for_selector(selector, timeout=timeout)
            return {"success": True, "selector": selector}

        elif action == "go_back":
            await self._page.go_back(timeout=timeout)
            return {"success": True, "url": self._page.url}

        elif action == "go_forward":
            await self._page.go_forward(timeout=timeout)
            return {"success": True, "url": self._page.url}

        return {"success": False, "error": f"Unknown action: {action}"}

    async def _close(self) -> Dict[str, Any]:
        """Close browser and cleanup."""
        try:
            if self._page:
                await self._page.close()
                self._page = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            return {"success": True, "message": "Browser closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _shutdown(self):
        await self._close()
