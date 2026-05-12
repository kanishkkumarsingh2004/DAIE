"""
Structured output utilities for DAIE agents.

Enables agents to return typed Pydantic model instances instead of raw
text strings, providing production-grade structured data extraction.

Usage::

    from pydantic import BaseModel, Field

    class SentimentResult(BaseModel):
        sentiment: str = Field(description="positive, negative, or neutral")
        confidence: float = Field(description="0.0 to 1.0")

    result = await agent.execute_task(
        "Analyze: 'DAIE is incredible!'",
        output_schema=SentimentResult,
    )
    assert isinstance(result, SentimentResult)
"""

import json
import logging
import re
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Maximum number of retry attempts when the LLM returns invalid structured output
MAX_SCHEMA_RETRIES = 2


class OutputValidationError(Exception):
    """
    Raised when the LLM output cannot be validated against the requested
    Pydantic output schema after all retry attempts.

    Attributes:
        raw_output: The raw LLM text that failed validation.
        schema_cls: The Pydantic model class that was expected.
        validation_errors: The Pydantic ``ValidationError`` (if available).
    """

    def __init__(
        self,
        message: str,
        raw_output: str = "",
        schema_cls: Optional[Type[BaseModel]] = None,
        validation_errors: Optional[ValidationError] = None,
    ):
        super().__init__(message)
        self.raw_output = raw_output
        self.schema_cls = schema_cls
        self.validation_errors = validation_errors


def build_schema_prompt(schema_cls: Type[BaseModel]) -> str:
    """
    Generate the LLM-facing instruction block from a Pydantic model.

    This creates a human-readable description of the required JSON schema
    that gets injected into the agent's system prompt when ``output_schema``
    is specified.

    Args:
        schema_cls: A Pydantic ``BaseModel`` subclass.

    Returns:
        A formatted string block to append to the system prompt.
    """
    schema = schema_cls.model_json_schema()
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    # Build a human-readable field description
    field_lines = []
    for name, prop in properties.items():
        field_type = prop.get("type", "any")
        description = prop.get("description", "")
        req_marker = " (REQUIRED)" if name in required else " (optional)"

        # Handle arrays
        if field_type == "array":
            items = prop.get("items", {})
            items_type = items.get("type", "any")
            field_type = f"array of {items_type}"

        # Handle enums
        if "enum" in prop:
            enum_vals = ", ".join(repr(v) for v in prop["enum"])
            description += f" One of: [{enum_vals}]"

        field_lines.append(f'  "{name}": "({field_type}) {description}"{req_marker}')

    schema_body = "{\n" + ",\n".join(field_lines) + "\n}"
    required_list = ", ".join(sorted(required)) if required else "(none)"

    return (
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "REQUIRED OUTPUT SCHEMA\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Your final answer MUST be a JSON object matching this exact schema:\n"
        f"{schema_body}\n\n"
        f"Required fields: {required_list}\n\n"
        'Put the JSON object as the value of the "answer" field in your response.\n'
        "Do NOT wrap it in markdown code fences. Return RAW JSON only.\n"
    )


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract the first valid JSON object from raw LLM text.

    Handles code fences, leading prose, and nested braces.
    """
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

    def try_parse(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    # Try the whole string
    result = try_parse(text)
    if isinstance(result, dict):
        return result

    # Find first valid JSON object via brace matching
    search_from = 0
    while True:
        start = text.find("{", search_from)
        if start == -1:
            break
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    result = try_parse(candidate)
                    if isinstance(result, dict):
                        return result
                    break
        search_from = start + 1

    return None


def parse_and_validate(raw: str, schema_cls: Type[BaseModel]) -> BaseModel:
    """
    Parse raw LLM output and validate it against a Pydantic model.

    The function first attempts to extract a JSON object from the raw text.
    If the JSON contains an ``"answer"`` key whose value is itself a dict,
    that inner dict is used for validation (matching the ReAct answer format).

    Args:
        raw: Raw text from the LLM.
        schema_cls: The Pydantic ``BaseModel`` subclass to validate against.

    Returns:
        A validated instance of ``schema_cls``.

    Raises:
        OutputValidationError: If no valid JSON can be extracted or if
            Pydantic validation fails.
    """
    data = _extract_json(raw)

    if data is None:
        raise OutputValidationError(
            f"Could not extract JSON from LLM output for schema {schema_cls.__name__}",
            raw_output=raw,
            schema_cls=schema_cls,
        )

    # If the LLM wrapped the schema inside the ReAct {"answer": {...}} format,
    # unwrap it
    if "answer" in data and isinstance(data["answer"], dict):
        data = data["answer"]
    elif "answer" in data and isinstance(data["answer"], str):
        # The LLM might have stringified the JSON inside "answer"
        inner = _extract_json(data["answer"])
        if inner is not None:
            data = inner

    try:
        return schema_cls.model_validate(data)
    except ValidationError as e:
        raise OutputValidationError(
            f"LLM output does not match schema {schema_cls.__name__}: {e}",
            raw_output=raw,
            schema_cls=schema_cls,
            validation_errors=e,
        )


def build_retry_prompt(raw: str, error: OutputValidationError) -> str:
    """
    Build a correction prompt to send back to the LLM after a validation failure.

    Args:
        raw: The raw LLM output that failed validation.
        error: The ``OutputValidationError`` containing validation details.

    Returns:
        A prompt string asking the LLM to fix its output.
    """
    error_details = str(error.validation_errors) if error.validation_errors else str(error)

    return (
        "Your previous response did not match the required output schema.\n\n"
        f"Your response was:\n{raw[:500]}\n\n"
        f"Validation errors:\n{error_details}\n\n"
        "Please fix your response and return ONLY a valid JSON object "
        "matching the required schema. No prose, no markdown, no code fences."
    )
