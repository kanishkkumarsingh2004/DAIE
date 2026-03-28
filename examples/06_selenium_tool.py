# Configure LLM
# IMPORTANT: Use a more capable model for better tool usage
# llama3.2:1b may struggle with complex tool parameters
# Recommended: llama3.2:latest, mistral, or qwen2.5
set_llm(ollama_llm="llama3.2:1b", stream=True)

import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.tools import SeleniumChromeTool

# Configure LLM
set_llm(ollama_llm="llama3.2:1b", stream=True)


async def main():
    print("=" * 60)
    print("  Selenium Browser Automation Demo")
    print("=" * 60)
    print("\nTROUBLESHOOTING Chrome Driver Errors:")
    print("  If you see 'DevToolsActivePort file doesn't exist':")
    print("  1. Check Chrome is installed: google-chrome --version")
    print("  2. Update ChromeDriver: pip install --upgrade webdriver-manager")
    print("  3. Try non-headless mode: set headless=False")
    print("  4. Use direct tool example (more reliable)")
    print("  5. Check Chrome version matches ChromeDriver version")

    # ──────────────────────────────────────────────
    # 1. Create an agent with Selenium tool
    # ──────────────────────────────────────────────
    agent = Agent(config=AgentConfig(
        name="BrowserBot",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt=(
            "You are a web automation expert. You can browse websites, "
            "extract data, fill forms, and take screenshots using the "
            "Selenium Chrome browser tool."
            "\n\nIMPORTANT: When using the selenium_chrome tool, you MUST provide the 'action' parameter."
            "\nAvailable actions: open_url, find_element, click, type, get_text, screenshot, execute_script, navigate, get_cookies, set_cookie, new_tab, close_tab"
            "\nExample: {\"action\": \"open_url\", \"url\": \"https://example.com\"}"
            "\nExample: {\"action\": \"find_element\", \"element_selector\": \"h1\", \"selector_type\": \"css\"}"
        ),
    ))

    # Add Selenium tool to the agent
    selenium_tool = SeleniumChromeTool()
    agent.add_tool(selenium_tool)

    await agent.start()

    # ──────────────────────────────────────────────
    # 2. Basic web scraping example
    # ──────────────────────────────────────────────
    print("\n[1] Basic Web Scraping - Getting page title and URL")

    result = await agent.execute_task(
        "Open https://example.com and tell me the page title and current URL"
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 3. Element interaction example
    # ──────────────────────────────────────────────
    print("\n[2] Element Interaction - Finding and reading elements")

    result = await agent.execute_task(
        "Go to https://example.com and find the main heading element. "
        "Tell me what text it contains."
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 4. Screenshot capture example
    # ──────────────────────────────────────────────
    print("\n[3] Screenshot Capture - Taking a screenshot of the page")

    result = await agent.execute_task(
        "Navigate to https://example.com and take a screenshot. "
        "Save it as 'example_screenshot.png'"
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 5. JavaScript execution example
    # ──────────────────────────────────────────────
    print("\n[4] JavaScript Execution - Running custom JavaScript")

    result = await agent.execute_task(
        "Go to https://example.com and execute JavaScript to get the "
        "page title. Return the result."
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 6. Multi-tab management example
    # ──────────────────────────────────────────────
    print("\n[5] Multi-Tab Management - Opening and managing tabs")

    result = await agent.execute_task(
        "Open https://example.com in the current tab, then open a new tab "
        "with https://httpbin.org/get. Switch back to the first tab and "
        "tell me the URL."
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 7. Navigation example
    # ──────────────────────────────────────────────
    print("\n[6] Navigation - Using back, forward, and refresh")

    result = await agent.execute_task(
        "Go to https://example.com, then navigate to https://httpbin.org/get, "
        "then go back to the previous page. Tell me the current URL."
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 8. Cookie management example
    # ──────────────────────────────────────────────
    print("\n[7] Cookie Management - Getting and setting cookies")

    result = await agent.execute_task(
        "Go to https://example.com, get all cookies, then set a custom "
        "cookie named 'test_cookie' with value 'hello_world'. "
        "Verify the cookie was set."
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 9. Complex automation task
    # ──────────────────────────────────────────────
    print("\n[8] Complex Automation - Multi-step web task")

    result = await agent.execute_task(
        "Perform these steps:\n"
        "1. Go to https://httpbin.org/forms/post\n"
        "2. Find the customer name input field and type 'John Doe'\n"
        "3. Find the telephone input field and type '555-1234'\n"
        "4. Find the email input field and type 'john@example.com'\n"
        "5. Take a screenshot of the filled form\n"
        "6. Tell me what you did"
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # 10. Data extraction example
    # ──────────────────────────────────────────────
    print("\n[9] Data Extraction - Scraping structured data")

    result = await agent.execute_task(
        "Go to https://httpbin.org/html and extract all the text content "
        "from the page. Return the main content."
    )
    print(f"    Result: {result}")

    # ──────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Demo complete! Cleaning up...")
    print("=" * 60)

    await agent.stop()


# ──────────────────────────────────────────────
# Direct tool usage example (without agent)
# ──────────────────────────────────────────────
async def direct_tool_example():
    """Example of using SeleniumChromeTool directly without an agent."""
    print("\n" + "=" * 60)
    print("  Direct Tool Usage Example")
    print("=" * 60)
    print("\nNOTE: If Chrome driver fails, try setting headless=False")

    tool = SeleniumChromeTool()

    # Open a URL
    print("\n[1] Opening URL...")
    try:
        result = await tool._execute({
            "action": "open_url",
            "url": "https://example.com",
            "headless": True,  # Set to False if you get Chrome driver errors
        })
        print(f"    Page title: {result.get('page_title')}")
        print(f"    Current URL: {result.get('current_url')}")
    except Exception as e:
        print(f"    Error: {e}")
        print("    Try setting headless=False or check Chrome installation")
        return

    # Get page source
    print("\n[2] Getting page source...")
    try:
        result = await tool._execute({
            "action": "get_page_source",
        })
        page_source = result.get('page_source', '')
        print(f"    Page source length: {len(page_source)} characters")
    except Exception as e:
        print(f"    Error: {e}")

    # Find element
    print("\n[3] Finding element...")
    try:
        result = await tool._execute({
            "action": "find_element",
            "element_selector": "h1",
            "selector_type": "css",
        })
        print(f"    Element text: {result.get('element_text')}")
    except Exception as e:
        print(f"    Error: {e}")

    # Take screenshot
    print("\n[4] Taking screenshot...")
    try:
        result = await tool._execute({
            "action": "screenshot",
            "screenshot_path": "direct_screenshot.png",
        })
        print(f"    Screenshot saved: {result.get('screenshot_path')}")
    except Exception as e:
        print(f"    Error: {e}")

    # Execute JavaScript
    print("\n[5] Executing JavaScript...")
    try:
        result = await tool._execute({
            "action": "execute_script",
            "script": "return document.title;",
        })
        print(f"    JavaScript result: {result.get('script_result')}")
    except Exception as e:
        print(f"    Error: {e}")

    # Get cookies
    print("\n[6] Getting cookies...")
    try:
        result = await tool._execute({
            "action": "get_cookies",
        })
        print(f"    Cookies: {result.get('cookies')}")
    except Exception as e:
        print(f"    Error: {e}")

    print("\n" + "=" * 60)
    print("  Direct tool example complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the agent-based example
    asyncio.run(main())

    # Uncomment to run the direct tool example
    # asyncio.run(direct_tool_example())
