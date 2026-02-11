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
    ElementNotInteractableException,
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
            description="Comprehensive Selenium Chrome browser automation tool - use this for web scraping, browser automation, testing, form filling, data extraction, and any task requiring browser interaction",
            category=ToolCategory.BROWSER_AUTOMATION,
            version="2.0.0",
            author="Decentralized AI Ecosystem",
            capabilities=[
                "browser_automation",
                "web_scraping",
                "selenium",
                "chrome",
                "web_testing",
                "form_filling",
                "data_extraction",
                "page_navigation",
                "element_interaction",
                "javascript_execution",
                "screenshot_capture",
                "cookies_management",
                "tabs_management",
            ],
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="URL to open in the browser",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform - comprehensive browser automation operations",
                    required=True,
                    default="open_url",
                    choices=[
                        "open_url",
                        "find_element",
                        "find_elements",
                        "click",
                        "type",
                        "clear",
                        "get_text",
                        "get_attribute",
                        "screenshot",
                        "screenshot_element",
                        "execute_script",
                        "navigate",
                        "get_page_source",
                        "get_title",
                        "get_url",
                        "get_cookies",
                        "set_cookie",
                        "delete_cookie",
                        "delete_all_cookies",
                        "switch_to_frame",
                        "switch_to_default_content",
                        "switch_to_window",
                        "new_tab",
                        "close_tab",
                        "scroll_to_element",
                        "scroll_by",
                        "wait_for_element",
                        "wait_for_text",
                        "select_dropdown",
                        "check_checkbox",
                        "uncheck_checkbox",
                        "get_window_handles",
                    ],
                ),
                ToolParameter(
                    name="element_selector",
                    type="string",
                    description="CSS selector or XPath for finding elements",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="selector_type",
                    type="string",
                    description="Type of selector (css or xpath)",
                    required=False,
                    default="css",
                    choices=["css", "xpath"],
                ),
                ToolParameter(
                    name="text",
                    type="string",
                    description="Text to type into an element or text to search for",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="script",
                    type="string",
                    description="JavaScript code to execute",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="navigate_action",
                    type="string",
                    description="Navigation action (back, forward, refresh)",
                    required=False,
                    default=None,
                    choices=["back", "forward", "refresh"],
                ),
                ToolParameter(
                    name="screenshot_path",
                    type="string",
                    description="File path to save screenshot",
                    required=False,
                    default="screenshot.png",
                ),
                ToolParameter(
                    name="headless",
                    type="boolean",
                    description="Whether to run Chrome in headless mode (no GUI)",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="window_size",
                    type="string",
                    description="Window size (width,height) - e.g., '1920,1080'",
                    required=False,
                    default="1920,1080",
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="Timeout for operations in seconds",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="attribute_name",
                    type="string",
                    description="Name of attribute to get or set",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="attribute_value",
                    type="string",
                    description="Value of attribute to set",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="cookie_name",
                    type="string",
                    description="Name of cookie to get, set, or delete",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="cookie_value",
                    type="string",
                    description="Value of cookie to set",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="cookie_domain",
                    type="string",
                    description="Domain for cookie",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="cookie_path",
                    type="string",
                    description="Path for cookie",
                    required=False,
                    default="/",
                ),
                ToolParameter(
                    name="frame_selector",
                    type="string",
                    description="Selector or index of frame/iframe to switch to",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="window_handle",
                    type="string",
                    description="Window handle or tab index to switch to",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="dropdown_value",
                    type="string",
                    description="Value or text of option to select from dropdown",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="dropdown_by",
                    type="string",
                    description="Method to select dropdown option (value, text, index)",
                    required=False,
                    default="value",
                    choices=["value", "text", "index"],
                ),
                ToolParameter(
                    name="scroll_x",
                    type="number",
                    description="Horizontal scroll distance",
                    required=False,
                    default=0,
                ),
                ToolParameter(
                    name="scroll_y",
                    type="number",
                    description="Vertical scroll distance",
                    required=False,
                    default=0,
                ),
                ToolParameter(
                    name="wait_time",
                    type="number",
                    description="Time to wait in seconds",
                    required=False,
                    default=5,
                ),
            ],
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
                service=Service(ChromeDriverManager().install()), options=chrome_options
            )

            timeout = params.get("timeout", 30)
            self.wait = WebDriverWait(self.driver, timeout)

            logger.debug("Chrome webdriver initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Chrome webdriver: {e}")
            raise

    def _find_element(
        self, selector: str, selector_type: str = "css", timeout: Optional[float] = None
    ):
        """
        Find an element using CSS selector or XPath
        """
        try:
            wait = self.wait
            if timeout is not None:
                wait = WebDriverWait(self.driver, timeout)

            if selector_type == "css":
                element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            else:
                element = wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            return element
        except TimeoutException:
            raise Exception(f"Element not found within timeout: {selector}")
        except Exception as e:
            raise Exception(f"Error finding element {selector}: {e}")

    def _find_elements(self, selector: str, selector_type: str = "css"):
        """
        Find multiple elements using CSS selector or XPath
        """
        try:
            if selector_type == "css":
                elements = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
            else:
                elements = self.wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
            return elements
        except TimeoutException:
            raise Exception(f"Elements not found within timeout: {selector}")
        except Exception as e:
            raise Exception(f"Error finding elements {selector}: {e}")

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

            elif action == "get_url":
                result["current_url"] = self.driver.current_url

            elif action == "find_element":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception(
                        "element_selector is required for find_element action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                result["element_found"] = True
                result["element_text"] = element.text

            elif action == "find_elements":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception(
                        "element_selector is required for find_elements action"
                    )
                selector_type = params.get("selector_type", "css")
                elements = self._find_elements(selector, selector_type)
                result["elements_found"] = len(elements)
                result["elements_text"] = [element.text for element in elements]

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
                    raise Exception(
                        "element_selector and text are required for type action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                element.clear()
                element.send_keys(text)
                result["typed_text"] = text

            elif action == "clear":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception("element_selector is required for clear action")
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                element.clear()
                result["cleared"] = True

            elif action == "get_text":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception("element_selector is required for get_text action")
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                result["text"] = element.text

            elif action == "get_attribute":
                selector = params.get("element_selector")
                attribute = params.get("attribute_name")
                if not selector or not attribute:
                    raise Exception(
                        "element_selector and attribute_name are required for get_attribute action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                result["attribute_value"] = element.get_attribute(attribute)

            elif action == "screenshot":
                screenshot_path = params.get("screenshot_path", "screenshot.png")
                self.driver.save_screenshot(screenshot_path)
                result["screenshot_path"] = screenshot_path
                result["screenshot_taken"] = True

            elif action == "screenshot_element":
                selector = params.get("element_selector")
                screenshot_path = params.get(
                    "screenshot_path", "element_screenshot.png"
                )
                if not selector:
                    raise Exception(
                        "element_selector is required for screenshot_element action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                element.screenshot(screenshot_path)
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

            elif action == "get_cookies":
                cookies = self.driver.get_cookies()
                result["cookies"] = cookies

            elif action == "set_cookie":
                cookie_name = params.get("cookie_name")
                cookie_value = params.get("cookie_value")
                if not cookie_name or not cookie_value:
                    raise Exception(
                        "cookie_name and cookie_value are required for set_cookie action"
                    )

                cookie = {
                    "name": cookie_name,
                    "value": cookie_value,
                    "domain": params.get("cookie_domain"),
                    "path": params.get("cookie_path", "/"),
                }
                self.driver.add_cookie(cookie)
                result["cookie_set"] = True

            elif action == "delete_cookie":
                cookie_name = params.get("cookie_name")
                if not cookie_name:
                    raise Exception("cookie_name is required for delete_cookie action")
                self.driver.delete_cookie(cookie_name)
                result["cookie_deleted"] = True

            elif action == "delete_all_cookies":
                self.driver.delete_all_cookies()
                result["all_cookies_deleted"] = True

            elif action == "switch_to_frame":
                frame_selector = params.get("frame_selector")
                if not frame_selector:
                    raise Exception(
                        "frame_selector is required for switch_to_frame action"
                    )
                try:
                    # Try to switch by index
                    frame_index = int(frame_selector)
                    self.driver.switch_to.frame(frame_index)
                except ValueError:
                    # Switch by selector
                    frame = self._find_element(
                        frame_selector, params.get("selector_type", "css")
                    )
                    self.driver.switch_to.frame(frame)
                result["switched_to_frame"] = True

            elif action == "switch_to_default_content":
                self.driver.switch_to.default_content()
                result["switched_to_default"] = True

            elif action == "new_tab":
                self.driver.execute_script("window.open('', '_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                result["new_tab_opened"] = True
                result["window_handle"] = self.driver.current_window_handle

            elif action == "close_tab":
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    result["tab_closed"] = True
                else:
                    result["tab_closed"] = False
                    result["message"] = "Cannot close last tab"

            elif action == "switch_to_window":
                window_handle = params.get("window_handle")
                if not window_handle:
                    raise Exception(
                        "window_handle is required for switch_to_window action"
                    )
                try:
                    # Try to switch by index
                    window_index = int(window_handle)
                    self.driver.switch_to.window(
                        self.driver.window_handles[window_index]
                    )
                except ValueError:
                    # Switch by handle
                    self.driver.switch_to.window(window_handle)
                result["switched_to_window"] = True
                result["current_url"] = self.driver.current_url

            elif action == "get_window_handles":
                result["window_handles"] = self.driver.window_handles
                result["current_window_handle"] = self.driver.current_window_handle

            elif action == "scroll_to_element":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception(
                        "element_selector is required for scroll_to_element action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", element
                )
                result["scrolled_to_element"] = True

            elif action == "scroll_by":
                x = params.get("scroll_x", 0)
                y = params.get("scroll_y", 0)
                self.driver.execute_script(f"window.scrollBy({x}, {y});")
                result["scrolled_by"] = {"x": x, "y": y}

            elif action == "wait_for_element":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception(
                        "element_selector is required for wait_for_element action"
                    )
                selector_type = params.get("selector_type", "css")
                wait_time = params.get("wait_time", 5)
                element = self._find_element(selector, selector_type, wait_time)
                result["element_found"] = True

            elif action == "wait_for_text":
                selector = params.get("element_selector")
                text = params.get("text")
                if not selector or not text:
                    raise Exception(
                        "element_selector and text are required for wait_for_text action"
                    )
                selector_type = params.get("selector_type", "css")
                wait_time = params.get("wait_time", 5)
                element = self._find_element(selector, selector_type, wait_time)
                result["text_found"] = text in element.text

            elif action == "select_dropdown":
                from selenium.webdriver.support.ui import Select

                selector = params.get("element_selector")
                dropdown_value = params.get("dropdown_value")
                if not selector or not dropdown_value:
                    raise Exception(
                        "element_selector and dropdown_value are required for select_dropdown action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                select = Select(element)

                select_by = params.get("dropdown_by", "value")
                if select_by == "value":
                    select.select_by_value(dropdown_value)
                elif select_by == "text":
                    select.select_by_visible_text(dropdown_value)
                elif select_by == "index":
                    select.select_by_index(int(dropdown_value))

                result["dropdown_selected"] = dropdown_value

            elif action == "check_checkbox":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception(
                        "element_selector is required for check_checkbox action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                if not element.is_selected():
                    element.click()
                result["checkbox_checked"] = True

            elif action == "uncheck_checkbox":
                selector = params.get("element_selector")
                if not selector:
                    raise Exception(
                        "element_selector is required for uncheck_checkbox action"
                    )
                selector_type = params.get("selector_type", "css")
                element = self._find_element(selector, selector_type)
                if element.is_selected():
                    element.click()
                result["checkbox_unchecked"] = True

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
