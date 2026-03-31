# Changelog

All notable changes to the Decentralized AI Ecosystem (DAIE) library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2026-03-31
### Added
- **Zero-Dependency Core**: Replaced several external dependencies (`requests`, `python-dotenv`, `rich`, `typer`) with in-house, lightweight implementations (`http_client`, `env`, `console`, `cli.core`).
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

## [1.0.4] - 2026-03-31
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
- **Secure File Transfers**: Base64-encoded encrypted file transfers between agents.

## [1.0.0] - 2026-03-20
### Added
- Initial core release of Decentralized AI Ecosystem.
- Basic Agent and Node structure.
- NATS JetStream integration for basic message passing.
