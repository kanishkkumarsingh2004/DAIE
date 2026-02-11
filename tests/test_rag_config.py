#!/usr/bin/env python3
"""
Test script for the new RAG configuration parameters
"""

import os
import tempfile
from daie.config import SystemConfig
from daie.agents.config import AgentConfig


def test_system_config_rag_params():
    """Test that SystemConfig has RAG parameters"""
    config = SystemConfig()
    
    # Check default values
    assert hasattr(config, "rag_document_path")
    assert config.rag_document_path is None
    assert hasattr(config, "enable_rag")
    assert config.enable_rag is False
    
    # Test setting values
    test_path = "/test/path"
    config = SystemConfig(rag_document_path=test_path, enable_rag=True)
    assert config.rag_document_path == test_path
    assert config.enable_rag is True
    
    # Test validation
    errors = config.validate()
    assert "rag_document_path" in errors
    assert "Must be a valid directory path" in errors["rag_document_path"]
    
    print("✅ SystemConfig RAG parameters test passed")


def test_agent_config_rag_params():
    """Test that AgentConfig has RAG parameters"""
    config = AgentConfig()
    
    # Check default values
    assert hasattr(config, "rag_document_path")
    assert config.rag_document_path is None
    assert hasattr(config, "enable_rag")
    assert config.enable_rag is False
    
    # Test setting values
    test_path = "/test/path"
    config = AgentConfig(rag_document_path=test_path, enable_rag=True)
    assert config.rag_document_path == test_path
    assert config.enable_rag is True
    
    # Test validation
    errors = config.validate()
    assert "RAG document path must be a valid directory" in errors
    
    print("✅ AgentConfig RAG parameters test passed")


def test_temporary_directory_validation():
    """Test validation with a temporary directory"""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # System config test
        system_config = SystemConfig(rag_document_path=temp_dir, enable_rag=True)
        errors = system_config.validate()
        assert "rag_document_path" not in errors
        
        # Agent config test
        agent_config = AgentConfig(rag_document_path=temp_dir, enable_rag=True)
        errors = agent_config.validate()
        assert "RAG document path must be a valid directory" not in errors
        
        print("✅ Temporary directory validation test passed")


def test_from_dict():
    """Test from_dict method with RAG parameters"""
    data = {
        "rag_document_path": "/test/documents",
        "enable_rag": True
    }
    
    system_config = SystemConfig.from_dict(data)
    assert system_config.rag_document_path == "/test/documents"
    assert system_config.enable_rag is True
    
    agent_config = AgentConfig.from_dict(data)
    assert agent_config.rag_document_path == "/test/documents"
    assert agent_config.enable_rag is True
    
    print("✅ from_dict method test passed")


def test_to_dict():
    """Test to_dict method with RAG parameters"""
    system_config = SystemConfig(rag_document_path="/test/documents", enable_rag=True)
    system_dict = system_config.to_dict()
    assert system_dict["rag_document_path"] == "/test/documents"
    assert system_dict["enable_rag"] is True
    
    agent_config = AgentConfig(rag_document_path="/test/documents", enable_rag=True)
    agent_dict = agent_config.to_dict()
    assert agent_dict["rag_document_path"] == "/test/documents"
    assert agent_dict["enable_rag"] is True
    
    print("✅ to_dict method test passed")


if __name__ == "__main__":
    print("Testing RAG configuration parameters...")
    test_system_config_rag_params()
    test_agent_config_rag_params()
    test_temporary_directory_validation()
    test_from_dict()
    test_to_dict()
    print("\n✅ All RAG configuration tests passed!")
