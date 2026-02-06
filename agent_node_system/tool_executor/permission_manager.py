#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Permission Manager

This module provides functionality for managing tool execution permissions.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PermissionManager:
    """
    Permission Manager
    
    Provides functionality for managing tool execution permissions.
    """
    
    def __init__(self):
        """Initialize the permission manager"""
        self.permissions = {}
        self.default_permission = False
        logger.info("Permission manager initialized")
    
    def check_permission(self, tool_name: str) -> bool:
        """
        Check if a tool can be executed
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            bool: True if permission granted, False otherwise
        """
        try:
            # Check specific tool permissions
            if tool_name in self.permissions:
                return self.permissions[tool_name]
            
            # Return default permission if no specific rule
            logger.debug(f"Using default permission for tool {tool_name}")
            return self.default_permission
        except Exception as e:
            logger.error(f"Failed to check permission for tool {tool_name}: {e}")
            return False
    
    def grant_permission(self, tool_name: str) -> bool:
        """
        Grant permission to execute a tool
        
        Args:
            tool_name: Name of the tool to grant permission for
            
        Returns:
            bool: True if permission granted successfully
        """
        try:
            self.permissions[tool_name] = True
            logger.info(f"Permission granted for tool {tool_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to grant permission for tool {tool_name}: {e}")
            return False
    
    def revoke_permission(self, tool_name: str) -> bool:
        """
        Revoke permission to execute a tool
        
        Args:
            tool_name: Name of the tool to revoke permission for
            
        Returns:
            bool: True if permission revoked successfully
        """
        try:
            self.permissions[tool_name] = False
            logger.info(f"Permission revoked for tool {tool_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke permission for tool {tool_name}: {e}")
            return False
    
    def set_default_permission(self, allow: bool) -> bool:
        """
        Set the default permission for all tools
        
        Args:
            allow: True to allow by default, False to deny by default
            
        Returns:
            bool: True if default permission set successfully
        """
        try:
            self.default_permission = allow
            logger.info(f"Default permission set to {allow}")
            return True
        except Exception as e:
            logger.error(f"Failed to set default permission: {e}")
            return False
    
    def get_permissions(self) -> Dict[str, bool]:
        """
        Get all permission settings
        
        Returns:
            dict: Dictionary of tool permissions
        """
        return self.permissions.copy()
    
    def load_permissions(self, permissions: Dict[str, bool]) -> bool:
        """
        Load permissions from a dictionary
        
        Args:
            permissions: Dictionary of tool permissions
            
        Returns:
            bool: True if permissions loaded successfully
        """
        try:
            self.permissions = permissions.copy()
            logger.info("Permissions loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load permissions: {e}")
            return False
    
    def clear_permissions(self) -> bool:
        """
        Clear all permission settings
        
        Returns:
            bool: True if permissions cleared successfully
        """
        try:
            self.permissions.clear()
            logger.info("Permissions cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear permissions: {e}")
            return False
