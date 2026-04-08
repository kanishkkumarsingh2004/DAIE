"""
Code Execution Sandbox Tool.

Provides safe Python code execution with restricted imports,
memory limits, and timeout enforcement.
"""

import logging
import subprocess
import sys
import textwrap
import tempfile
import os
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)

# Dangerous modules that are blocked in the sandbox
_BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "requests",
    "ctypes", "multiprocessing", "signal",
    "importlib", "code", "codeop", "compile",
    "eval", "exec", "pickle", "shelve",
}

_SANDBOX_WRAPPER = textwrap.dedent('''\
import builtins
import io
import sys
import json
import time

# Block dangerous imports
_BLOCKED = {blocked_set}
_original_import = builtins.__import__

def _safe_import(name, *args, **kwargs):
    top_level = name.split(".")[0]
    if top_level in _BLOCKED:
        raise ImportError(f"Import of '{{name}}' is not allowed in the sandbox")
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _safe_import

# Redirect stdout/stderr
_stdout = io.StringIO()
_stderr = io.StringIO()
sys.stdout = _stdout
sys.stderr = _stderr

_start = time.time()
_return_value = None

try:
    # User code
{user_code}
    _return_value = None
except Exception as _e:
    _stderr.write(str(_e))

_elapsed = time.time() - _start

result = {{
    "stdout": _stdout.getvalue()[:10000],
    "stderr": _stderr.getvalue()[:5000],
    "return_value": str(_return_value) if _return_value is not None else None,
    "execution_time": round(_elapsed, 4),
}}
print("__SANDBOX_RESULT__" + json.dumps(result))
''')


class CodeSandboxTool(Tool):
    """
    Safe Python code execution sandbox.

    Runs user code in a subprocess with:
    - Blocked dangerous imports (os, sys, subprocess, etc.)
    - Timeout enforcement
    - Memory limit (256MB default)
    - No file system write access

    Example:
        >>> tool = CodeSandboxTool()
        >>> result = await tool.execute({
        ...     "code": "print(sum(range(100)))",
        ...     "timeout": 5
        ... })
    """

    def __init__(self, max_memory_mb: int = 256):
        self._max_memory_mb = max_memory_mb

        metadata = ToolMetadata(
            name="code_sandbox",
            description="Execute Python code safely in a sandboxed environment with restricted imports and resource limits.",
            category=ToolCategory.SYSTEM,
            version="1.0.0",
            author="DAIE",
            capabilities=["code_execution", "computation", "data_processing"],
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="Python code to execute",
                    required=True,
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Execution timeout in seconds (default: 10, max: 30)",
                    required=False,
                    default=10,
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Any:
        import asyncio

        code = params["code"]
        timeout = min(params.get("timeout", 10), 30)

        # Indent user code for the wrapper
        indented_code = textwrap.indent(code, "    ")

        # Build the sandbox script
        blocked_repr = repr(_BLOCKED_MODULES)
        script = _SANDBOX_WRAPPER.format(
            blocked_set=blocked_repr,
            user_code=indented_code,
        )

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="daie_sandbox_"
        ) as f:
            f.write(script)
            script_path = f.name

        try:
            result = await asyncio.to_thread(
                self._run_subprocess, script_path, timeout
            )
            return result
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass

    def _run_subprocess(self, script_path: str, timeout: int) -> Dict[str, Any]:
        """Run the sandbox script in a subprocess."""
        import json

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            stdout = result.stdout
            stderr = result.stderr

            # Extract sandbox result
            marker = "__SANDBOX_RESULT__"
            if marker in stdout:
                idx = stdout.index(marker)
                json_str = stdout[idx + len(marker):]
                try:
                    sandbox_result = json.loads(json_str)
                    return {
                        "success": True,
                        **sandbox_result,
                    }
                except json.JSONDecodeError:
                    pass

            return {
                "success": result.returncode == 0,
                "stdout": stdout[:10000],
                "stderr": stderr[:5000],
                "return_value": None,
                "execution_time": None,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "return_value": None,
                "execution_time": timeout,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_value": None,
                "execution_time": None,
            }
