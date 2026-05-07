# Tools

DAIE provides a powerful tool system that allows agents to interact with the external world. Tools are the "hands" of the agent — they can read/write files, make HTTP requests, automate browsers, and more.

## Pre-built Tools

| Tool | Description | Import |
|------|-------------|--------|
| `FileManagerTool` | Create, read, write, delete, copy, move files and directories | `from daie.tools import FileManagerTool` |
| `APICallTool` | HTTP GET / POST / PUT / DELETE / PATCH requests | `from daie.tools import APICallTool` |
| `HTTPGetTool` | Simplified HTTP GET | `from daie.tools import HTTPGetTool` |
| `HTTPPostTool` | Simplified HTTP POST | `from daie.tools import HTTPPostTool` |
| `SeleniumChromeTool` | Full Chrome browser automation | `from daie.tools import SeleniumChromeTool` |
| `A2ASendFileTool` | Transfer files between agents with ChaCha20 E2E encryption | `from daie.tools.a2a_file import A2ASendFileTool` |
| `A2ASendMessageTool` | Send messages between agents | `from daie.tools.a2a import A2ASendMessageTool` |
| `A2ADelegateTaskTool` | Delegate tasks to other agents via ACP | `from daie.tools.a2a import A2ADelegateTaskTool` |

---

## FileManagerTool

Create, read, write, delete, copy, move files and directories.

```python
from daie.tools import FileManagerTool

fm = FileManagerTool()

# Create a file
await fm.execute({"action": "create_file", "path": "notes.txt", "content": "hello"})

# Read a file
result = await fm.execute({"action": "read_file", "path": "notes.txt"})
print(result["content"])

# List directory contents
result = await fm.execute({"action": "list_contents", "path": ".", "recursive": False})

# Delete a file
await fm.execute({"action": "delete_file", "path": "notes.txt"})

# Copy a file
await fm.execute({"action": "copy_file", "source": "notes.txt", "destination": "notes_backup.txt"})

# Move a file
await fm.execute({"action": "move_file", "source": "notes.txt", "destination": "archive/notes.txt"})
```

### Available Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `create_file` | `path`, `content` | Create a new file with content |
| `read_file` | `path` | Read file contents |
| `delete_file` | `path` | Delete a file |
| `copy_file` | `source`, `destination` | Copy a file |
| `move_file` | `source`, `destination` | Move a file |
| `list_contents` | `path`, `recursive` | List directory contents |
| `create_directory` | `path` | Create a directory |

---

## APICallTool

Make HTTP requests to external APIs.

```python
from daie.tools import APICallTool

api = APICallTool()

# GET request
result = await api.execute({
    "url": "https://api.github.com/users/octocat",
    "method": "GET",
    "headers": {"Accept": "application/json"},
})
print(result["json"])

# POST request
result = await api.execute({
    "url": "https://api.example.com/data",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": {"key": "value"},
})
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `string` | Yes | Target URL |
| `method` | `string` | No | HTTP method (GET, POST, PUT, DELETE, PATCH). Default: GET |
| `headers` | `object` | No | Request headers |
| `body` | `object/string` | No | Request body |
| `timeout` | `number` | No | Request timeout in seconds. Default: 30 |

---

## HTTPGetTool & HTTPPostTool

Simplified tools for common HTTP operations.

```python
from daie.tools import HTTPGetTool, HTTPPostTool

# HTTP GET
get_tool = HTTPGetTool()
result = await get_tool.execute({
    "url": "https://api.example.com/data",
    "headers": {"Accept": "application/json"},
})

# HTTP POST
post_tool = HTTPPostTool()
result = await post_tool.execute({
    "url": "https://api.example.com/data",
    "body": {"key": "value"},
    "headers": {"Content-Type": "application/json"},
})
```

---

## SeleniumChromeTool

Full Chrome browser automation using Selenium.

```python
from daie.tools import SeleniumChromeTool

browser = SeleniumChromeTool()

# Open a URL
await browser.execute({"action": "open_url", "url": "https://example.com", "headless": True})

# Get page title
result = await browser.execute({"action": "get_title"})
print(result["page_title"])

# Take a screenshot
await browser.execute({"action": "screenshot", "screenshot_path": "page.png"})

# Get page source
result = await browser.execute({"action": "get_source"})

# Click an element
await browser.execute({"action": "click", "selector": "#my-button"})

# Type text
await browser.execute({"action": "type", "selector": "#my-input", "text": "Hello"})

# Close browser
await browser.execute({"action": "close"})
```

### Available Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `open_url` | `url`, `headless` | Open a URL in Chrome |
| `get_title` | — | Get page title |
| `get_source` | — | Get page HTML source |
| `screenshot` | `screenshot_path` | Take a screenshot |
| `click` | `selector` | Click an element |
| `type` | `selector`, `text` | Type text into an element |
| `close` | — | Close the browser |

---

## A2A Tools (Agent-to-Agent)

### A2ASendFileTool

Transfer files between agents over the P2P network with ChaCha20 end-to-end encryption.

```python
from daie.tools.a2a_file import A2ASendFileTool

file_tool = A2ASendFileTool()
file_tool.set_agent(agent)  # Bind to agent

result = await file_tool.execute({
    "receiver_id": "other-agent-id",
    "file_path": "document.pdf",
    "message": "Here's the document you requested",
})
```

### A2ASendMessageTool

Send messages between agents.

```python
from daie.tools.a2a import A2ASendMessageTool

msg_tool = A2ASendMessageTool()
msg_tool.set_agent(agent)

result = await msg_tool.execute({
    "target_agent_id": "other-agent-id",
    "message": "Hello from Agent Alpha!",
})
```

### A2ADelegateTaskTool

Delegate tasks to other agents using the Agent Connect Protocol (ACP).

```python
from daie.tools.a2a import A2ADelegateTaskTool

delegate_tool = A2ADelegateTaskTool()
delegate_tool.set_agent(agent)

result = await delegate_tool.execute({
    "target_agent_id": "specialist-agent-id",
    "task_payload": {"task": "Analyze this data and provide insights"},
    "mapping_rules": {},  # Optional ACP I/O mapping
})
```

---

## Custom Tools with @tool Decorator

Create custom tools by decorating any function:

```python
from daie.tools import tool

@tool(name="reverse_string", description="Reverses a string")
async def reverse_string(text: str) -> str:
    return text[::-1]

# Add to agent
agent.add_tool(reverse_string)

# Use in ReAct loop
result = await agent.execute_task("Reverse the word 'decentralized'")
```

### Decorator Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Tool name (used by LLM to call the tool) |
| `description` | `string` | Yes | Tool description (shown to LLM) |
| `category` | `ToolCategory` | No | Tool category. Default: `ToolCategory.CUSTOM` |

### Function Parameters

The function's parameters are automatically extracted and included in the tool schema:

```python
@tool(name="search", description="Search for information")
async def search(query: str, max_results: int = 5) -> str:
    # query is required, max_results is optional with default 5
    results = perform_search(query, max_results)
    return json.dumps(results)
```

---

## Tool Base Class

For more complex tools, extend the `Tool` base class:

```python
from daie.tools import Tool, ToolMetadata, ToolParameter, ToolCategory

class MyCustomTool(Tool):
    def __init__(self):
        metadata = ToolMetadata(
            name="my_custom_tool",
            description="Does something useful",
            category=ToolCategory.CUSTOM,
            parameters=[
                ToolParameter(
                    name="input",
                    type="string",
                    description="Input data",
                    required=True
                ),
                ToolParameter(
                    name="options",
                    type="object",
                    description="Optional settings",
                    required=False,
                    default={}
                ),
            ]
        )
        super().__init__(metadata)

    async def _execute(self, params: dict) -> dict:
        input_data = params.get("input")
        options = params.get("options", {})
        
        # Your tool logic here
        result = process(input_data, options)
        
        return {"success": True, "result": result}
```

### ToolMetadata

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | — | Tool name |
| `description` | `str` | — | Tool description |
| `category` | `ToolCategory` | `GENERAL` | Tool category |
| `version` | `str` | `"1.0.0"` | Tool version |
| `author` | `str` | `"Unknown"` | Tool author |
| `capabilities` | `List[str]` | `[]` | Tool capabilities |
| `parameters` | `List[ToolParameter]` | `[]` | Tool parameters |

### ToolParameter

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | — | Parameter name |
| `type` | `str` | `"string"` | Parameter type |
| `description` | `str` | `""` | Parameter description |
| `required` | `bool` | `True` | Whether parameter is required |
| `default` | `Any` | `None` | Default value |
| `choices` | `List[Any] \| None` | `None` | Allowed values |

### ToolCategory

```python
from daie.tools import ToolCategory

ToolCategory.GENERAL
ToolCategory.SEARCH
ToolCategory.FILE
ToolCategory.SYSTEM
ToolCategory.WEB
ToolCategory.DATABASE
ToolCategory.API
ToolCategory.BROWSER_AUTOMATION
ToolCategory.CUSTOM
```

---

## ToolRegistry

The `ToolRegistry` manages tool discovery and registration:

```python
from daie.tools import ToolRegistry

registry = ToolRegistry()

# Register a tool
registry.register(my_tool)

# Get a tool by name
tool = registry.get("my_tool_name")

# List all tools
tools = registry.list_tools()
```

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [LLM Configuration](llm.md) — Multi-provider LLM setup
- [Communication](communication.md) — P2P networking and file transfers
- [RAG](rag.md) — Retrieval-Augmented Generation
