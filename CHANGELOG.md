All notable changes to the Decentralized AI Ecosystem (DAIE) library will be documented in this file.

## [1.0.7] - 2026-04-25
### Added
- **Architectural Stack Documentation**: Formalized the 4-layer DAIE ecosystem stack (L1-L4) in `README.md` and `docs/`.
    - **L1: Agent Layer**: Individual cognitive units.
    - **L2: Coordination Layer**: Orchestrators and Parliaments.
    - **L3: Node Layer**: Hybrid infrastructure and resource management.
    - **L4: System Layer**: Global multi-node mesh and P2P routing.
- **Encapsulation Pattern**: Documented the cross-layer interaction model for decentralized AI systems.

## [1.0.6] - 2026-04-15
### Added
- **Parliament Multi-Agent Architecture**: Deliberative consensus loops allowing agent teams to "debate" and reach democratic or peer-reviewed conclusions.
- **Distributed Deliberation**: Support for running a single Parliament across multiple physical P2P nodes via `CommunicationManager` broadcasting.
- **Persistent SQLite Storage**: Concurrent-safe disk persistence for agent memory (episodic and semantic) using SQLite with WAL (Write-Ahead Logging).
- **Hardened Tool Ecosystem**:
    - **Safe Code Execution**: Native async sandbox with POSIX resource limits (`RLIMIT_CPU`, `RLIMIT_AS`) and blocked dangerous imports.
    - **Advanced Playwright**: Intelligent HTML-to-Markdown extraction while stripping non-content elements.
    - **Schema Discovery**: Database tools can now self-inspect table schemas for autonomous SQL correction.
    - **Async-First Search**: Web search tool refactored for native async with robust Tavily fallback and User-Agent rotation.
- **Parallel Executor**: New core utility to run any number of agents or tasks in parallel with managed concurrency thresholds.

### Changed
- Refactored `CodeSandboxTool` to use `asyncio.create_subprocess_exec` for superior performance and non-blocking I/O.
- Enhanced `CommunicationManager` with agent-specific broadcast handlers for distributed state synchronization.
- Updated `Agent.stop()` to ensure ALL sub-components (Memory, Tools, Comm) are shut down cleanly.

## [1.0.5] - 2026-04-03
### Fixed — Production Stability Release
- **Orchestrator A2A flow**: Fixed broken agent-to-agent delegation. Task payload was double-wrapped (`{"task": {"task": "..."}}`) causing sub-agents to receive a dict instead of a plain string. Now recursively unwraps nested dicts until a plain string is extracted.
- **Task reply path**: Sub-agents were replying via `agent.send_message(AgentMessage)` which silently failed when `communication_manager` was not set as an attribute. All reply paths now go directly through `comm_mgr.send_message()`.
- **Task message race condition**: Task messages were dispatched with `asyncio.create_task()` (fire-and-forget), causing the delegation future to time out before the reply arrived. Task messages are now `await`ed directly inside `_handle_message`.
- **`broadcast_message` hardcoded IDs**: `broadcast_message` was sending to hardcoded `["agent2", "agent3"]` instead of all registered agents. Fixed to iterate over `self._agents`.
- **Dead inbox in `_send_message_internal`**: Every message was stored in a `self._inbox` dict that nothing ever read for delivery. Removed the dead inbox; delivery is now purely push-based via `_handle_message`.
- **`CommunicationManager._handle_message`**: Removed stale `import inspect` and replaced with `asyncio.create_task(agent._handle_message(message))` directly since `_handle_message` is always `async def`.
- **Memory pickle not created**: `Agent.stop()` never called `memory_manager.stop()`, so the final flush to disk never happened. Fixed by calling `self.memory_manager.stop()` during agent shutdown.
- **`MemoryManager.log_chat_history` broken auto-start**: Removed broken logic that tried to call `self.start()` mid-conversation, which could cause double-initialization.
- **`MemoryManager.initialize_agent_memory`**: Fixed to only call `_load_agent_memory` when storage actually exists, preventing a no-op call when `persistent_memory=False`.
- **`BinaryFileStorage.save_agent_memory`**: Added atomic write using `.tmp` + `os.replace()` + `os.fsync()` to prevent corrupted pickle files on crash.
- **`HybridOrchestratorNode` double-start**: Agents were started directly AND again inside `orchestrator.start()`. Now the orchestrator handles all agent starts.
- **`ChatLoopConfig._send_message_with_retry`**: Fixed `AttributeError` crash when agent returned a non-string response (`response.startswith()` called on `None`/dict).
- **`NodeRegistry` writes `node_registry.json` to cwd**: Changed default `registry_file` to `None` (in-memory only). File persistence is now opt-in.
- **`LLMManager` stale class-level `_initialized`**: Removed redundant class-level attribute that shadowed the instance attribute set in `__new__`.
- **`AnthropicLLM` missing `last_usage` init**: Added `self.last_usage` initialization to prevent `AttributeError` before first LLM call.
- **`ToolRegistry.register` raised on duplicate**: Changed from raising `ValueError` to silently updating, preventing crashes when agents restart and re-register A2A tools.
- **`DecentralizedAISystem.stop`**: Was calling `await self.memory_manager.stop()` but `MemoryManager.stop()` is synchronous. Fixed to call `self.memory_manager.stop()` directly. Also wrapped each component stop in individual try/except so one failure doesn't prevent others from stopping.
- **File transfer reply path**: File rejection and acknowledgment replies used the broken `send_message(AgentMessage)` path. Fixed to use `comm_mgr.send_message()` directly.

### Changed
- **`pyproject.toml`**: Bumped to `1.0.5`, status `Production/Stable`, moved `pyaudio` to optional `[audio]` extra, relaxed version pins, added `[all]` extra, added project URLs.
- **`__version__`**: Updated to `1.0.5`.

## [1.0.5] - 2026-03-31
### Added
- **Lightweight Core**: Replaced several external dependencies (`requests`, `python-dotenv`, `rich`, `typer`) with in-house, lightweight implementations (`http_client`, `env`, `console`, `cli.core`).
- **In-House Tracing**: Removed OpenTelemetry in favor of a custom, lightweight tracing architecture in `daie.core.tracing`.
- **Enhanced Guardrails**: Implemented strict task-level token and tool-call guardrails directly in `AgentConfig`.
- **One-File Demo**: Added a comprehensive "Full Power" demonstration snippet to `README.md`.

### Changed
- **BREAKING**: Standardized Agent instantiation to use the `Agent(config=config)` pattern.
- **BREAKING**: Enforced mandatory asynchronous lifecycle synchronization; all agents and nodes must be started with `await start()` and stopped with `await stop()`.
- **Dependency Promotion**: `numpy`, `pydantic`, and `pydantic-settings` are now core dependencies to ensure production stability.
- **Documentation Overhaul**: Synchronized all `docs/` and `examples/` with the latest v1.0.5 API and async patterns.

### Removed
- `otel` (OpenTelemetry) as a core dependency.
- `requests`, `python-dotenv`, `rich`, and `typer` as core dependencies.

## [1.0.5] - 2026-03-31
### Added
- **Observability**: Added OpenTelemetry (OTel) support for distributed tracing across agent nodes.
- **Resilience**: Implemented Circuit Breaker pattern for P2P communication and configurable Retry policies.
- **Safety Guardrails**: 
    - Token-based rate limiting for P2P interactions.
    - LLM token limits per session/agent.
    - Configrable max tool-call iterations per task.
- **Tracing**: Instrumentation for `execute_task`, tool calls, and remote communication.

### Changed
- Enhanced `CommunicationManager` with resilience mechanisms.
- Updated `SystemConfig` and `AgentConfig` to support new production features.

## [1.0.3] - 2026-03-30
### Added
- **Asynchronous Lifecycle**: Fully migrated the entire library to an `async/await` architecture for `start()` and `stop()` methods.
- **Stability Sweep**: Production-grade stability improvements across core examples.

### Changed
- **BREAKING**: All lifecycle methods are now `async`. Synchronization logic for P2P networks was updated to handle concurrent async starts.
- Documentation updated to reflect mandatory `await` patterns.

## [1.0.2] - 2026-03-26
### Added
- **Orchestrator Architecture**: Flexible multi-agent coordination.
- **Decentralized RAG**: Agent-specific knowledge bases (RAG) with local document indexing.
- **Vision Integration**: Chat capabilities with local camera access and vision models (Ollama).
- **Classroom Demo**: Advanced simulation of multi-agent academic interactions.

## [1.0.1] - 2026-03-25
### Added
- **Persona-Driven Behavior**: Personality traits (gender, behavioral quirks) reflected in LLM prompts.
- **A2A / ACP Protocol**: Secure Agent-to-Agent (A2A) communication over P2P networks.
- **Tool Use**: Autonomous ReAct loop for agents to utilize CLI, File, and API tools.
- **File Transfers**: Base64-encoded file transfers between agents.

## [1.0.0] - 2026-03-20
### Added
- Initial core release of Decentralized AI Ecosystem.
- Basic Agent and Node structure.
- NATS JetStream integration for basic message passing.
