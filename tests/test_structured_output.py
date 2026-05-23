"""
Tests for structured agent output schemas.
"""

import json

import pytest
from pydantic import BaseModel, Field, ValidationError

from daie.agents.structured_output import (
    MAX_SCHEMA_RETRIES,
    OutputValidationError,
    build_retry_prompt,
    build_schema_prompt,
    parse_and_validate,
    _extract_json,
)


# ── test models ───────────────────────────────────────────────────────────────


class SentimentResult(BaseModel):
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(description="0.0 to 1.0")
    reasoning: str = Field(description="Why this sentiment was chosen")


class SimpleOutput(BaseModel):
    answer: str
    score: int


class NestedAddress(BaseModel):
    street: str
    city: str
    zip_code: str = Field(description="5-digit ZIP code")


class PersonOutput(BaseModel):
    name: str
    age: int
    address: NestedAddress


class OptionalFieldsModel(BaseModel):
    required_field: str
    optional_field: str = "default_value"


# ── build_schema_prompt ───────────────────────────────────────────────────────


def test_build_schema_prompt_contains_field_names():
    """Schema prompt contains all field names from the model."""
    prompt = build_schema_prompt(SentimentResult)
    assert "sentiment" in prompt
    assert "confidence" in prompt
    assert "reasoning" in prompt


def test_build_schema_prompt_contains_descriptions():
    """Schema prompt includes field descriptions."""
    prompt = build_schema_prompt(SentimentResult)
    assert "positive, negative, or neutral" in prompt
    assert "0.0 to 1.0" in prompt


def test_build_schema_prompt_marks_required_fields():
    """Schema prompt marks required fields."""
    prompt = build_schema_prompt(SentimentResult)
    assert "REQUIRED" in prompt


def test_build_schema_prompt_contains_instructions():
    """Schema prompt includes formatting instructions."""
    prompt = build_schema_prompt(SentimentResult)
    assert "REQUIRED OUTPUT SCHEMA" in prompt
    assert "answer" in prompt  # instructs to put in "answer" field
    assert "RAW JSON" in prompt


def test_build_schema_prompt_simple_model():
    """Schema prompt works for a simple model."""
    prompt = build_schema_prompt(SimpleOutput)
    assert "answer" in prompt
    assert "score" in prompt


# ── _extract_json ─────────────────────────────────────────────────────────────


def test_extract_json_plain():
    """Extract JSON from a plain JSON string."""
    result = _extract_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_extract_json_with_prose():
    """Extract JSON from text with leading prose."""
    result = _extract_json('Here is the result: {"key": "value"} and more text')
    assert result == {"key": "value"}


def test_extract_json_with_code_fence():
    """Extract JSON from markdown code fences."""
    result = _extract_json('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_extract_json_nested():
    """Extract JSON with nested objects."""
    raw = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
    result = _extract_json(raw)
    assert result["outer"]["inner"] == "value"
    assert result["list"] == [1, 2, 3]


def test_extract_json_returns_none_for_invalid():
    """Returns None when no valid JSON can be found."""
    assert _extract_json("no json here") is None
    assert _extract_json("") is None
    assert _extract_json("{invalid json}}}") is None


# ── parse_and_validate ────────────────────────────────────────────────────────


def test_parse_and_validate_valid_json():
    """parse_and_validate succeeds on valid JSON matching the schema."""
    raw = json.dumps({
        "sentiment": "positive",
        "confidence": 0.95,
        "reasoning": "Very enthusiastic language",
    })
    result = parse_and_validate(raw, SentimentResult)
    assert isinstance(result, SentimentResult)
    assert result.sentiment == "positive"
    assert result.confidence == 0.95


def test_parse_and_validate_wrapped_in_answer():
    """parse_and_validate unwraps the ReAct {"answer": {...}} format."""
    raw = json.dumps({
        "thought": "I analyzed the text",
        "answer": {
            "sentiment": "negative",
            "confidence": 0.8,
            "reasoning": "Uses negative words",
        },
    })
    result = parse_and_validate(raw, SentimentResult)
    assert isinstance(result, SentimentResult)
    assert result.sentiment == "negative"


def test_parse_and_validate_answer_as_json_string():
    """parse_and_validate handles answer as a JSON string."""
    inner = json.dumps({
        "sentiment": "neutral",
        "confidence": 0.5,
        "reasoning": "Mixed signals",
    })
    raw = json.dumps({"answer": inner})
    result = parse_and_validate(raw, SentimentResult)
    assert isinstance(result, SentimentResult)
    assert result.sentiment == "neutral"


def test_parse_and_validate_with_code_fence():
    """parse_and_validate handles JSON wrapped in markdown code fences."""
    raw = '```json\n{"sentiment": "positive", "confidence": 0.9, "reasoning": "Clear"}\n```'
    result = parse_and_validate(raw, SentimentResult)
    assert isinstance(result, SentimentResult)
    assert result.sentiment == "positive"


def test_parse_and_validate_with_prose():
    """parse_and_validate handles JSON mixed with prose."""
    raw = 'Here is my analysis:\n{"sentiment": "positive", "confidence": 0.85, "reasoning": "Good"}\nDone.'
    result = parse_and_validate(raw, SentimentResult)
    assert isinstance(result, SentimentResult)


def test_parse_and_validate_missing_fields():
    """parse_and_validate raises OutputValidationError on missing required fields."""
    raw = json.dumps({"sentiment": "positive"})  # missing confidence and reasoning
    with pytest.raises(OutputValidationError) as exc_info:
        parse_and_validate(raw, SentimentResult)
    assert exc_info.value.schema_cls is SentimentResult
    assert exc_info.value.validation_errors is not None


def test_parse_and_validate_wrong_type():
    """parse_and_validate raises OutputValidationError on type mismatch."""
    raw = json.dumps({
        "sentiment": "positive",
        "confidence": "not_a_float",
        "reasoning": "Test",
    })
    with pytest.raises(OutputValidationError):
        parse_and_validate(raw, SentimentResult)


def test_parse_and_validate_no_json():
    """parse_and_validate raises OutputValidationError when no JSON is found."""
    with pytest.raises(OutputValidationError) as exc_info:
        parse_and_validate("This is just plain text with no JSON", SentimentResult)
    assert "Could not extract JSON" in str(exc_info.value)


def test_parse_and_validate_simple_model():
    """parse_and_validate works with a simple model."""
    raw = json.dumps({"answer": "hello", "score": 42})
    result = parse_and_validate(raw, SimpleOutput)
    assert result.answer == "hello"
    assert result.score == 42


def test_parse_and_validate_nested_model():
    """parse_and_validate works with nested Pydantic models."""
    raw = json.dumps({
        "name": "Alice",
        "age": 30,
        "address": {
            "street": "123 Main St",
            "city": "Springfield",
            "zip_code": "12345",
        },
    })
    result = parse_and_validate(raw, PersonOutput)
    assert isinstance(result, PersonOutput)
    assert result.name == "Alice"
    assert isinstance(result.address, NestedAddress)
    assert result.address.city == "Springfield"


# ── OutputValidationError ─────────────────────────────────────────────────────


def test_output_validation_error_attributes():
    """OutputValidationError carries raw_output and schema_cls."""
    err = OutputValidationError(
        "test error",
        raw_output="bad json",
        schema_cls=SentimentResult,
    )
    assert err.raw_output == "bad json"
    assert err.schema_cls is SentimentResult
    assert str(err) == "test error"


def test_output_validation_error_with_validation_errors():
    """OutputValidationError can carry Pydantic ValidationError."""
    try:
        SentimentResult(sentiment="x")  # missing fields
    except ValidationError as ve:
        err = OutputValidationError(
            "validation failed",
            raw_output="{}",
            schema_cls=SentimentResult,
            validation_errors=ve,
        )
        assert err.validation_errors is not None


# ── build_retry_prompt ────────────────────────────────────────────────────────


def test_build_retry_prompt_contains_error():
    """build_retry_prompt includes the error details."""
    err = OutputValidationError(
        "missing fields",
        raw_output='{"bad": "json"}',
        schema_cls=SentimentResult,
    )
    prompt = build_retry_prompt('{"bad": "json"}', err)
    assert "missing fields" in prompt
    assert "fix" in prompt.lower()
    assert '{"bad": "json"}' in prompt


def test_build_retry_prompt_truncates_long_output():
    """build_retry_prompt truncates very long raw output."""
    long_output = "x" * 1000
    err = OutputValidationError("err", raw_output=long_output)
    prompt = build_retry_prompt(long_output, err)
    # Should not contain the full 1000 chars
    assert len(prompt) < 1000 + 500  # prompt overhead + truncated output


# ── constants ─────────────────────────────────────────────────────────────────


def test_max_schema_retries_is_positive():
    """MAX_SCHEMA_RETRIES should be a reasonable positive integer."""
    assert MAX_SCHEMA_RETRIES >= 1
    assert MAX_SCHEMA_RETRIES <= 5


# ── import from agents package ────────────────────────────────────────────────


def test_output_validation_error_importable_from_agents():
    """OutputValidationError is importable from the agents package."""
    from daie.agents import OutputValidationError as OVE
    assert OVE is OutputValidationError
