"""Tests for utils module."""

import pytest
import json
from daie.utils.common import generate_id, is_json, deep_merge, retry
from daie.utils.encryption import encrypt_data, decrypt_data, generate_encryption_key
from daie.utils.logger import setup_logger
from daie.utils.serialization import to_json, from_json, Serializer


class TestCommonUtils:
    """Tests for common utility functions."""

    def test_generate_id(self):
        """Test ID generation."""
        id1 = generate_id()
        id2 = generate_id()

        assert isinstance(id1, str)
        assert len(id1) > 0
        assert id1 != id2

    def test_is_json(self):
        """Test JSON validation."""
        valid_json = '{"key": "value"}'
        invalid_json = '{key: "value"}'

        assert is_json(valid_json) is True
        assert is_json(invalid_json) is False

    def test_retry_decorator(self):
        """Test retry decorator."""
        attempts = 0

        @retry
        def failing_func():
            nonlocal attempts
            attempts += 1
            raise Exception("Intentional failure")

        with pytest.raises(Exception):
            failing_func()

        assert attempts == 3

    def test_deep_merge(self):
        """Test deep merge functionality."""
        dict1 = {"a": 1, "b": {"c": 2, "d": 3}, "e": [4, 5]}

        dict2 = {"b": {"c": 20, "f": 6}, "e": [6, 7], "g": 8}

        merged = deep_merge(dict1, dict2)

        assert merged["a"] == 1
        assert merged["b"]["c"] == 20  # Overridden
        assert merged["b"]["d"] == 3  # Preserved
        assert merged["b"]["f"] == 6  # Added
        assert merged["e"] == [6, 7]  # Overridden
        assert merged["g"] == 8  # Added


class TestEncryptionUtils:
    """Tests for encryption utility functions."""

    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption."""
        key = generate_encryption_key()
        message = "This is a secret message"

        encrypted = encrypt_data(message, key)
        assert isinstance(encrypted, str)
        assert encrypted != message

        decrypted = decrypt_data(encrypted, key)
        assert decrypted == message

    def test_encrypt_decrypt_empty_data(self):
        """Test encryption with empty data."""
        key = generate_encryption_key()
        message = ""

        encrypted = encrypt_data(message, key)
        assert isinstance(encrypted, str)

        decrypted = decrypt_data(encrypted, key)
        assert decrypted == message

    def test_decrypt_with_wrong_key(self):
        """Test decryption with wrong key."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        message = "Secret message"

        encrypted = encrypt_data(message, key1)

        with pytest.raises(Exception):
            decrypt_data(encrypted, key2)


class TestLoggerUtils:
    """Tests for logger utility functions."""

    def test_setup_logger(self):
        """Test logger creation."""
        logger = setup_logger("test-logger")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_logger_methods(self, caplog):
        """Test logger methods."""
        logger = setup_logger("test-logger", level="DEBUG")

        logger.info("Info message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        assert "Info message" in caplog.text
        assert "Debug message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text


class TestSerializationUtils:
    """Tests for serialization utility functions."""

    def test_json_serialization(self):
        """Test JSON serialization/deserialization."""
        data = {
            "key1": "value1",
            "key2": 123,
            "key3": [1, 2, 3],
            "key4": {"nested": "value"},
        }

        serialized = to_json(data)
        assert isinstance(serialized, str)

        deserialized = from_json(serialized)
        assert deserialized == data

    def test_serializer_class(self):
        """Test Serializer class functionality."""
        data = {"key": "value"}
        serializer = Serializer()

        # Test JSON serialization
        json_str = serializer.serialize(data, "json")
        assert isinstance(json_str, str)
        assert '"key"' in json_str

        # Test deserialization
        obj = serializer.deserialize(json_str, "json")
        assert obj == data

    def test_serialize_deserialize_special_types(self):
        """Test serialization of special types."""
        from datetime import datetime

        data = {
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "none": None,
            "true": True,
            "false": False,
        }

        serialized = to_json(data)
        deserialized = from_json(serialized)

        assert isinstance(deserialized, dict)
        assert "timestamp" in deserialized


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_complete_encryption_workflow(self):
        """Test complete encryption workflow with serialization."""
        key = generate_encryption_key()
        data = {"message": "This is a secret message", "id": generate_id()}

        # Serialize and encrypt
        serialized = to_json(data)
        encrypted = encrypt_data(serialized, key)

        # Decrypt and deserialize
        decrypted = decrypt_data(encrypted, key)
        deserialized = from_json(decrypted)

        assert deserialized == data

    def test_retry_with_success(self):
        """Test retry decorator with successful operation."""
        attempts = 0

        @retry
        def eventually_successful():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise Exception("Temporary failure")
            return "Success!"

        result = eventually_successful()

        assert result == "Success!"
        assert attempts == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
