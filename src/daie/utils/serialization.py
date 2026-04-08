"""
Serialization and deserialization utility functions
"""

import json
import pickle
from typing import Any, Dict, Optional

import yaml


def to_json(obj: Any, indent: int = 2, sort_keys: bool = True) -> str:
    """
    Convert object to JSON string

    Args:
        obj: Object to serialize
        indent: Indentation for pretty printing
        sort_keys: Whether to sort keys

    Returns:
        JSON string representation
    """
    try:
        return json.dumps(obj, indent=indent, sort_keys=sort_keys, default=str)
    except Exception as e:
        raise Exception(f"JSON serialization failed: {e}")


def from_json(text: str) -> Any:
    """
    Parse JSON string to object

    Args:
        text: JSON string

    Returns:
        Parsed object
    """
    try:
        return json.loads(text)
    except Exception as e:
        raise Exception(f"JSON deserialization failed: {e}")


def extract_json(text: str) -> Any:
    """
    Robustly extract the first valid JSON object from a string.
    Handles code fences, leading/trailing prose, and partial wrapping.
    """
    import re
    if not text:
        return None

    # Clean up text - strip leading/trailing whitespace and code fences
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()

    def try_parse(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    # Try the whole string first
    res = try_parse(text)
    if res:
        return res

    # Try finding the largest block between { and }
    first_bracket = text.find("{")
    last_bracket = text.rfind("}")
    
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = text[first_bracket : last_bracket + 1]
        res = try_parse(candidate)
        if res:
            return res

    # Fallback: iterative search from start
    search_from = 0
    while True:
        start = text.find("{", search_from)
        if start == -1:
            break

        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    res = try_parse(candidate)
                    if res:
                        return res
                    break
        search_from = start + 1

    return None


def extract_conversational_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Fallback for when models emit "Thought: ... Answer: ..." instead of JSON.
    """
    import re
    if not text:
        return None

    # Try JSON extraction first
    json_res = extract_json(text)
    if json_res:
        return json_res

    # Fallback: parse plain-text "Thought: ... Answer: ..." or "Answer: ..." formats
    answer_match = re.search(
        r"(?:^|\n)\s*(?:Answer|ANSWER|Response|RESPONSE)\s*[:\-]\s*(.+)", text, re.DOTALL
    )
    if answer_match:
        answer_text = answer_match.group(1).strip()
        # Try to find thought if it exists before answer
        thought_match = re.search(
            r"(?:^|\n)\s*(?:Thought|THOUGHT|Thinking|Reasoning)\s*[:\-]\s*(.+?)(?:\n\s*(?:Answer|ANSWER|Response|RESPONSE))",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        thought_text = thought_match.group(1).strip() if thought_match else ""
        return {"thought": thought_text, "answer": answer_text}

    return None


def to_yaml(obj: Any, indent: int = 2) -> str:
    """
    Convert object to YAML string

    Args:
        obj: Object to serialize
        indent: Indentation for pretty printing

    Returns:
        YAML string representation
    """
    try:
        return yaml.dump(obj, default_flow_style=False, indent=indent)
    except Exception as e:
        raise Exception(f"YAML serialization failed: {e}")


def from_yaml(text: str) -> Any:
    """
    Parse YAML string to object

    Args:
        text: YAML string

    Returns:
        Parsed object
    """
    try:
        return yaml.safe_load(text)
    except Exception as e:
        raise Exception(f"YAML deserialization failed: {e}")


def to_pickle(obj: Any) -> bytes:
    """
    Serialize object to pickled bytes

    Args:
        obj: Object to serialize

    Returns:
        Pickled bytes
    """
    try:
        return pickle.dumps(obj)
    except Exception as e:
        raise Exception(f"Pickling failed: {e}")


def from_pickle(data: bytes) -> Any:
    """
    Deserialize pickled bytes to object

    Args:
        data: Pickled bytes

    Returns:
        Deserialized object
    """
    try:
        return pickle.loads(data)
    except Exception as e:
        raise Exception(f"Unpickling failed: {e}")


def load_json_file(file_path: str) -> Any:
    """
    Load JSON from file

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed object
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load JSON file: {e}")


def save_json_file(obj: Any, file_path: str, indent: int = 2, sort_keys: bool = True):
    """
    Save object to JSON file

    Args:
        obj: Object to save
        file_path: Path to save file
        indent: Indentation for pretty printing
        sort_keys: Whether to sort keys
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=indent, sort_keys=sort_keys, default=str)
    except Exception as e:
        raise Exception(f"Failed to save JSON file: {e}")


def load_yaml_file(file_path: str) -> Any:
    """
    Load YAML from file

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed object
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"Failed to load YAML file: {e}")


def save_yaml_file(obj: Any, file_path: str, indent: int = 2):
    """
    Save object to YAML file

    Args:
        obj: Object to save
        file_path: Path to save file
        indent: Indentation for pretty printing
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(obj, f, default_flow_style=False, indent=indent)
    except Exception as e:
        raise Exception(f"Failed to save YAML file: {e}")


def load_pickle_file(file_path: str) -> Any:
    """
    Load pickled object from file

    Args:
        file_path: Path to pickle file

    Returns:
        Deserialized object
    """
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise Exception(f"Failed to load pickle file: {e}")


def save_pickle_file(obj: Any, file_path: str):
    """
    Save object to pickle file

    Args:
        obj: Object to save
        file_path: Path to save file
    """
    try:
        with open(file_path, "wb") as f:
            pickle.dump(obj, f)
    except Exception as e:
        raise Exception(f"Failed to save pickle file: {e}")


def to_csv(data: list, headers: list = None) -> str:
    """
    Convert data to CSV format

    Args:
        data: List of dictionaries or lists
        headers: Optional column headers

    Returns:
        CSV string
    """
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers) if headers else csv.writer(output)

    if headers:
        writer.writeheader()

    for row in data:
        writer.writerow(row)

    return output.getvalue()


def from_csv(text: str, headers: list = None) -> list:
    """
    Parse CSV data to list

    Args:
        text: CSV string
        headers: Optional column headers

    Returns:
        List of dictionaries or lists
    """
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(text)) if headers else csv.reader(StringIO(text))
    return list(reader)


def format_json_for_display(data: Any, indent: int = 2, sort_keys: bool = True) -> str:
    """
    Format JSON for display with syntax highlighting

    Args:
        data: Data to format
        indent: Indentation
        sort_keys: Whether to sort keys

    Returns:
        Formatted JSON string
    """
    try:
        import json

        return json.dumps(data, indent=indent, sort_keys=sort_keys, default=str)
    except Exception:
        return str(data)


def format_yaml_for_display(data: Any, indent: int = 2) -> str:
    """
    Format YAML for display with syntax highlighting

    Args:
        data: Data to format
        indent: Indentation

    Returns:
        Formatted YAML string
    """
    try:
        import yaml

        return yaml.dump(data, default_flow_style=False, indent=indent)
    except Exception:
        return str(data)


class Serializer:
    """
    Utility class for managing serialization formats

    Example:
        >>> from daie.utils.serialization import Serializer

        >>> serializer = Serializer()
        >>> data = {'name': 'test', 'value': 42}
        >>>
        >>> # Serialize to JSON
        >>> json_str = serializer.serialize(data, 'json')
        >>>
        >>> # Deserialize from YAML
        >>> obj = serializer.deserialize(yaml_str, 'yaml')
    """

    def __init__(self):
        """Initialize serializer with support for various formats"""
        self._format_handlers = {
            "json": (to_json, from_json),
            "yaml": (to_yaml, from_yaml),
            "pickle": (to_pickle, from_pickle),
            "csv": (to_csv, from_csv),
        }

    def serialize(self, obj: Any, format: str = "json", **kwargs) -> Any:
        """
        Serialize object to specified format

        Args:
            obj: Object to serialize
            format: Output format (json, yaml, pickle, csv)
            **kwargs: Additional serialization parameters

        Returns:
            Serialized data
        """
        if format not in self._format_handlers:
            raise ValueError(f"Unsupported format: {format}")

        serializer, _ = self._format_handlers[format]
        return serializer(obj, **kwargs)

    def deserialize(self, data: Any, format: str = "json", **kwargs) -> Any:
        """
        Deserialize data from specified format

        Args:
            data: Data to deserialize
            format: Input format (json, yaml, pickle, csv)
            **kwargs: Additional deserialization parameters

        Returns:
            Deserialized object
        """
        if format not in self._format_handlers:
            raise ValueError(f"Unsupported format: {format}")

        _, deserializer = self._format_handlers[format]
        return deserializer(data, **kwargs)

    def load_from_file(self, file_path: str, format: str = None) -> Any:
        """
        Load data from file with automatic format detection

        Args:
            file_path: Path to file
            format: Explicit format specification

        Returns:
            Deserialized object
        """
        if not format:
            import os

            format = os.path.splitext(file_path)[1][1:].lower()

        if format == "json":
            return load_json_file(file_path)
        elif format == "yaml" or format == "yml":
            return load_yaml_file(file_path)
        elif format == "pickle" or format == "pkl":
            return load_pickle_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {format}")

    def save_to_file(self, obj: Any, file_path: str, format: str = None, **kwargs):
        """
        Save data to file with automatic format detection

        Args:
            obj: Object to save
            file_path: Path to save file
            format: Explicit format specification
            **kwargs: Additional serialization parameters
        """
        if not format:
            import os

            format = os.path.splitext(file_path)[1][1:].lower()

        if format == "json":
            save_json_file(obj, file_path, **kwargs)
        elif format == "yaml" or format == "yml":
            save_yaml_file(obj, file_path, **kwargs)
        elif format == "pickle" or format == "pkl":
            save_pickle_file(obj, file_path)
        else:
            raise ValueError(f"Unsupported file format: {format}")
