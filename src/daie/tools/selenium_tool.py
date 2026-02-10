"""
Selenium tool for automating Chrome browser
"""

import logging
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager

from daie.tools.tool import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class SeleniumChromeTool(Tool):
    """
    A tool for automating Chrome browser using Selenium.

    This tool supports various browser automation operations such as:
    - Opening URLs
    - Finding and interacting with elements
    - Taking screenshots
    - Executing JavaScript
    - Navigating browser history
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="selenium_chrome",
            description="Tool for automating Chrome browser using Selenium - use this for operations like web scraping, browser automation, opening URLs, interacting with web pages, taking screenshots, executing JavaScript, or any task that requires a web browser",
            category=ToolCategory.BROWSER_AUTOMATION,
            version="1.0.0",
            author="Decentralized AI Ecosystem",
            capabilities=[
                "browser_automation",
                "web_scraping",
                "selenium",
                "chrome",
                "web_testing"
            ],
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="URL to open in the browser",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform (open_url, find_element, click, type, screenshot, execute_script, navigate)",
                    required=True,
                    default="open_url",
                    choices=[
                        "open_url",
                        "find_element",
                        "click",
                        "type",
                        "screenshot",
                        "execute_script",
                        "navigate",
                        "get_page_source",
                        "get_title"
                    ]
                ),
                ToolParameter(
                    name="element_selector",
                    type="string",
                    description="CSS selector or XPath for finding elements",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="selector_type",
                    type="string",
                    description="Type of selector (css or xpath)",
                    required=False,
                    default="css",
                    choices=["css", "xpath"]
                ),
                ToolParameter(
                    name="text",
                    type="string",
                    description="Text to type into an element",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="script",
                    type="string",
                    description="JavaScript code to execute",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="navigate_action",
                    type="string",
                    description="Navigation action (back, forward, refresh)",
                    required=False,
                    default=None,
                    choices=["back", "forward", "refresh"]
                ),
                ToolParameter(
                    name="screenshot_path",
                    type="string",
                    description="File path to save screenshot",
                    required=False,
                    default="screenshot.png"
                ),
                ToolParameter(
                    name="headless",
                    type="boolean",
                    description="Whether to run Chrome in headless mode (no GUI)",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="window_size",
                    type="string",
                    description="Window size (width,height) - e.g., '1920,1080'",
                    required=False,
                    default="1920,1080"
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="Timeout for operations in seconds",
                    required=False,
                    default=30
                )
            ]
        )
        super().__init__(metadata)
        self.driver = None
        self.wait = None

    def _initialize_driver(self, params: Dict[str, Any]) -> None:
        """
        Initialize Chrome webdriver
        """
        if self.driver is not None:
            return

        try:
            chrome_options = Options()
            headless = params.get("headless", True)
            if headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")

            window_size = params.get("window_size", "1920,1080")
            chrome_options.add_argument(f"--window-size={window_size}")

            logger.debug("Initializing Chrome webdriver")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            timeout = params.get("timeout", 30)
            self.wait = WebDriverWait(self.driver, timeout)

            logger.debug("Chrome webdriver initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Chrome webdriver: {e}")
            raise

    def _find_element(self, selector: str, selector_type: str = "css"):
        """
        Find an element using CSS selector or XPath
        """
        try:
            if selector_type == "css":
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            else:
                element = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            return element
        except TimeoutException:
            raise Exception(f"Element not found within timeout: {selector}")
        except Exception as e:
            raise Exception(f"Error finding element {selector}: {e}")

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Selenium Chrome browser automation

        Args:
            params: Parameters for the automation task

        Returns:
            Dictionary containing the operation results

        Raises:
            Exception: If the automation operation fails
        """
        try:
            self._initialize_driver(params)

            action = params.get("action")
            result = {"success": True}

            if action == "open_url":
                url = params.get("url")
                if not url:
                    raise Exception("URL is required for open_url action")
                logger.debug(f"Opening URL: {url}")
                self.driver.get(url)
                result["page_title"] = self.driver.title
                result["current_url"] = self.driver.current_url

            elif action == "get_page_source":
                result["page_source"] = self.driver.page_source

            elif action == "get_title":
                result["page_title"] = self.driver.title

            elif action == "find_element":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception("element_selector is required for find_element action")
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                result["element_found"] = True
                result["element_text"] = element.text

            elif action == "click":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception("element_selector is required for click action")
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                element.click()
                result["clicked"] = True

            elif action == "type":
                selector = params.get("element_selector")
                text = params.get("text")
                if not selector or not text:
                    raise Exception("element_selector and text are required for type action")
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                element.clear()
                element.send_keys(text)
                result["typed_text"] = text

            elif action == "screenshot":
                screenshot_path = params.get("screenshot_path", "screenshot.png")
                self.driver.save_screenshot(screenshot_path)
                result["screenshot_path"] = screenshot_path
                result["screenshot_taken"] = True

            elif action == "execute_script":
                script = params.get("script")
                if not script:
                    raise Exception("script is required for execute_script action")
                script_result = self.driver.execute_script(script)
                result["script_result"] = script_result

            elif action == "navigate":
                navigate_action = params.get("navigate_action")
                if not navigate_action:
                    raise Exception("navigate_action is required for navigate action")
                if navigate_action == "back":
                    self.driver.back()
                elif navigate_action == "forward":
                    self.driver.forward()
                elif navigate_action == "refresh":
                    self.driver.refresh()
                result["navigate_action"] = navigate_action
                result["current_url"] = self.driver.current_url

            else:
                raise Exception(f"Unknown action: {action}")

            logger.debug(f"Selenium action '{action}' completed successfully")
            return result

        except Exception as e:
            logger.error(f"Selenium action failed: {e}")
            raise

    def __del__(self):
        """
        Cleanup webdriver instance
        """
        if self.driver is not None:
            try:
                self.driver.quit()
                logger.debug("Chrome webdriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing Chrome webdriver: {e}")


class SeleniumToolkit:
    """
    Collection of Selenium tools for easy access
    """

    @staticmethod
    def get_tools() -> list:
        """
        Get all Selenium tools

        Returns:
            List of Selenium tool instances
        """
        return [SeleniumChromeTool()]
