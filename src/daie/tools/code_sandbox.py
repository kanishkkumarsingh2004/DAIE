"""
Code Execution Sandbox Tool.

Provides safe Python code execution with restricted imports,
memory limits, and timeout enforcement.
"""

import logging
import sys
import textwrap
import tempfile
import os
import json
import asyncio
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)

# Dangerous modules that are blocked in the sandbox
_BLOCKED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "pathlib",
    "socket",
    "http",
    "urllib",
    "requests",
    "ctypes",
    "multiprocessing",
    "signal",
    "threading",
    "importlib",
    "code",
    "codeop",
    "compile",
    "eval",
    "exec",
    "pickle",
    "shelve",
    "marshal",
    "pty",
    "platform",
    "resource",
    "gc",
}

_SANDBOX_WRAPPER = textwrap.dedent("""\
import builtins
import io
import sys
import json
import time

# Save original stdout
_real_stdout = sys.stdout

# Block dangerous imports
_BLOCKED = {blocked_set}
_original_import = builtins.__import__
_original_exec = builtins.exec
_original_eval = builtins.eval

def _safe_import(name, *args, **kwargs):
    top_level = name.split(".")[0]
    if top_level in _BLOCKED:
        raise ImportError(f"Import of '{{name}}' is not allowed in the sandbox")
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _safe_import

# Block eval/exec
def _blocked_func(*args, **kwargs):
    raise RuntimeError("This function is disabled in the sandbox")

builtins.eval = _blocked_func
builtins.exec = _blocked_func

# Redirect stdout/stderr
_stdout = io.StringIO()
_stderr = io.StringIO()
sys.stdout = _stdout
sys.stderr = _stderr

_start = time.time()
_return_value = None

try:
    # Set localized return value capture if possible
    _locals = {{}}
    # Use the original exec to run the user code
    _original_exec({user_code_repr}, {{'__builtins__': builtins}}, _locals)
    # Heuristic: if 'result' is in locals, use it as return value
    _return_value = _locals.get('result')
except Exception as _e:
    _stderr.write(str(_e))

_elapsed = time.time() - _start

result = {{
    "stdout": _stdout.getvalue()[:10000],
    "stderr": _stderr.getvalue()[:5000],
    "return_value": str(_return_value) if _return_value is not None else None,
    "execution_time": round(_elapsed, 4),
}}

# Write result to original stdout
_real_stdout.write("__SANDBOX_RESULT__" + json.dumps(result))
""")


class CodeSandboxTool(Tool):
    """
    Safe Python code execution sandbox.

    Runs user code in a subprocess with:
    - Blocked dangerous imports (os, sys, subprocess, etc.)
    - Timeout enforcement (SIGKILL if needed)
    - Resource limits (CPU time and memory) via POSIX resource module
    - Native async execution tracking

    Example:
        >>> tool = CodeSandboxTool()
        >>> result = await tool.execute({
        ...     "code": "result = sum(range(100))",
        ...     "timeout": 5
        ... })
    """

    def __init__(self, max_memory_mb: int = 256):
        self._max_memory_mb = max_memory_mb

        metadata = ToolMetadata(
            name="code_sandbox",
            description="Execute Python code safely in a sandboxed environment with restricted imports and resource limits.",
            category=ToolCategory.SYSTEM,
            version="1.1.0",
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
        code = params["code"]
        timeout = min(params.get("timeout", 10), 30)

        # Build the sandbox script
        blocked_repr = repr(_BLOCKED_MODULES)
        script = _SANDBOX_WRAPPER.format(
            blocked_set=blocked_repr,
            user_code_repr=repr(code),
        )

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="daie_sandbox_"
        ) as f:
            f.write(script)
            script_path = f.name

        try:
            # Prepare preexec_fn for resource limits (Linux only)
            preexec = None
            if sys.platform != "win32":

                def set_limits():
                    try:
                        import resource

                        # Set CPU time limit (soft=timeout, hard=timeout+2)
                        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout + 2))
                        # Set address space limit (memory)
                        mem_bytes = self._max_memory_mb * 1024 * 1024
                        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                    except (ImportError, ValueError):
                        pass

                preexec = set_limits

            # Run via asyncio.create_subprocess_exec
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                preexec_fn=preexec,
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(), timeout=timeout + 1
                )
                stdout = stdout_data.decode()
                stderr = stderr_data.decode()
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "return_value": None,
                    "execution_time": timeout,
                }

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
                "success": process.returncode == 0,
                "stdout": stdout[:10000],
                "stderr": stderr[:5000],
                "return_value": None,
                "execution_time": None,
            }

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_value": None,
                "execution_time": None,
            }
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass
