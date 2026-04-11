import logging
from typing import Any, Dict, Optional

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)


class PlaywrightTool(Tool):
    """
    Premium Browser Automation Tool using Playwright.

    Supports advanced interactions and content extraction:
    - Navigation, Clicking, Typing, JS Evaluation.
    - Screenshot and PDF generation.
    - 'extract_content': Intelligently cleans page HTML for LLM reasoning.

    Example:
        >>> tool = PlaywrightTool()
        >>> result = await tool.execute({"action": "navigate", "url": "https://news.ycombinator.com"})
        >>> result = await tool.execute({"action": "extract_content"})
    """

    def __init__(self, headless: bool = True, user_agent: Optional[str] = None):
        self._headless = headless
        self._user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None

        metadata = ToolMetadata(
            name="playwright",
            description="Advanced browser automation for web scraping, interaction, and data extraction.",
            category=ToolCategory.BROWSER_AUTOMATION,
            version="1.1.0",
            author="DAIE",
            capabilities=[
                "browser_automation",
                "web_scraping",
                "visual_verification",
                "content_extraction",
            ],
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform",
                    required=True,
                    choices=[
                        "navigate",
                        "click",
                        "type",
                        "screenshot",
                        "extract_content",
                        "get_html",
                        "evaluate_js",
                        "wait_for_selector",
                        "go_back",
                        "go_forward",
                        "close",
                    ],
                ),
                ToolParameter(
                    name="url",
                    type="string",
                    description="URL to navigate to",
                    required=False,
                ),
                ToolParameter(
                    name="selector",
                    type="string",
                    description="CSS selector for elements",
                    required=False,
                ),
                ToolParameter(
                    name="text",
                    type="string",
                    description="Text input for fields",
                    required=False,
                ),
                ToolParameter(
                    name="js_code",
                    type="string",
                    description="JavaScript to execute on page",
                    required=False,
                ),
                ToolParameter(
                    name="wait_until",
                    type="string",
                    description="Wait condition for navigation",
                    choices=["load", "domcontentloaded", "networkidle", "commit"],
                    required=False,
                    default="domcontentloaded",
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Timeout in milliseconds (default: 30000)",
                    required=False,
                    default=30000,
                ),
            ],
        )
        super().__init__(metadata)

    async def _ensure_browser(self):
        """Lazily initialize browser and shared context."""
        if self._page is not None:
            if not self._page.is_closed():
                return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
            self._context = await self._browser.new_context(user_agent=self._user_agent)

        self._page = await self._context.new_page()
        logger.info("Playwright session initialized")

    async def _execute(self, params: Dict[str, Any]) -> Any:
        action = params["action"]
        timeout = params.get("timeout", 30000)

        if action == "close":
            return await self._close()

        try:
            await self._ensure_browser()
        except Exception as e:
            return {"success": False, "error": f"Failed to initialize browser: {e}"}

        try:
            if action == "navigate":
                url = params.get("url")
                wait_until = params.get("wait_until", "domcontentloaded")
                if not url:
                    return {"success": False, "error": "URL required"}
                await self._page.goto(url, timeout=timeout, wait_until=wait_until)
                return {"success": True, "title": await self._page.title(), "url": self._page.url}

            elif action == "click":
                selector = params.get("selector")
                if not selector:
                    return {"success": False, "error": "Selector required"}
                await self._page.click(selector, timeout=timeout)
                return {"success": True, "selector": selector}

            elif action == "type":
                selector = params.get("selector")
                text = params.get("text", "")
                if not selector:
                    return {"success": False, "error": "Selector required"}
                await self._page.fill(selector, text, timeout=timeout)
                return {"success": True, "selector": selector}

            elif action == "screenshot":
                path = params.get(
                    "text", "screenshot.png"
                )  # reusing 'text' param if name matches or just use default
                await self._page.screenshot(path=path, full_page=True)
                return {"success": True, "path": path}

            elif action == "extract_content":
                # Intelligent cleaning script
                clean_script = """
                () => {
                    const body = document.body.cloneNode(true);
                    const toRemove = ['script', 'style', 'nav', 'footer', 'iframe', 'header', 'aside', 'noscript', 'svg'];
                    toRemove.forEach(tag => body.querySelectorAll(tag).forEach(el => el.remove()));
                    return body.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 0).join('\\n');
                }
                """
                content = await self._page.evaluate(clean_script)
                return {
                    "success": True,
                    "title": await self._page.title(),
                    "url": self._page.url,
                    "content": content[:15000],  # Limit to avoid context overflow
                }

            elif action == "get_html":
                selector = params.get("selector", "body")
                html = await self._page.inner_html(selector)
                return {"success": True, "html": html[:10000]}

            elif action == "evaluate_js":
                js_code = params.get("js_code")
                if not js_code:
                    return {"success": False, "error": "js_code required"}
                result = await self._page.evaluate(js_code)
                return {"success": True, "result": result}

            elif action == "wait_for_selector":
                selector = params.get("selector")
                if not selector:
                    return {"success": False, "error": "Selector required"}
                await self._page.wait_for_selector(selector, timeout=timeout)
                return {"success": True, "selector": selector}

            elif action == "go_back":
                await self._page.go_back(timeout=timeout)
                return {"success": True, "url": self._page.url}

        except Exception as e:
            logger.error(f"Playwright error during {action}: {e}")
            return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Unknown action: {action}"}

    async def _close(self) -> Dict[str, Any]:
        """Close context and browser."""
        try:
            if self._page and not self._page.is_closed():
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            self._page = self._context = self._browser = self._playwright = None
            return {"success": True, "message": "Playwright session closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _shutdown(self):
        await self._close()
