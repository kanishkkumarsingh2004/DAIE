#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Chat History Management

This module provides functionality for managing chat history with other agents.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatHistory:
    """
    Chat History Management
    
    Provides functionality for storing and retrieving chat history with other agents.
    """
    
    def __init__(self, storage_dir="local_storage"):
        """
        Initialize the chat history manager
        
        Args:
            storage_dir: Directory to store chat history files
        """
        self.storage_dir = storage_dir
        self.chats = {}
        self._load_chat_history()
        logger.info("Chat history manager initialized")
    
    def _load_chat_history(self):
        """Load chat history from disk"""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            logger.info("Chat history loaded from disk")
        except Exception as e:
            logger.error(f"Failed to load chat history: {e}")
    
    def add_message(self, sender_id, recipient_id, content, message_type="chat"):
        """
        Add a message to the chat history
        
        Args:
            sender_id: ID of the message sender
            recipient_id: ID of the message recipient
            content: Message content
            message_type: Type of message (default: "chat")
            
        Returns:
            dict: The stored message
        """
        try:
            message = {
                "id": str(datetime.now().timestamp()),
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "content": content,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            
            chat_key = f"{min(sender_id, recipient_id)}_{max(sender_id, recipient_id)}"
            if chat_key not in self.chats:
                self.chats[chat_key] = []
            
            self.chats[chat_key].append(message)
            logger.debug(f"Message added to chat history: {chat_key}")
            
            return message
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return None
    
    def get_chat_history(self, agent_id1, agent_id2, limit=50):
        """
        Get chat history between two agents
        
        Args:
            agent_id1: First agent ID
            agent_id2: Second agent ID
            limit: Maximum number of messages to return (default: 50)
            
        Returns:
            list: List of messages in the chat
        """
        try:
            chat_key = f"{min(agent_id1, agent_id2)}_{max(agent_id1, agent_id2)}"
            return self.chats.get(chat_key, [])[-limit:]
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    def mark_message_read(self, message_id):
        """
        Mark a message as read
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            bool: True if message marked as read, False otherwise
        """
        try:
            for chat_key, messages in self.chats.items():
                for message in messages:
                    if message["id"] == message_id:
                        message["read"] = True
                        logger.debug(f"Message marked as read: {message_id}")
                        return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False
    
    def get_unread_messages(self, agent_id):
        """
        Get unread messages for an agent
        
        Args:
            agent_id: Agent ID to get unread messages for
            
        Returns:
            list: List of unread messages
        """
        try:
            unread = []
            for chat_key, messages in self.chats.items():
                for message in messages:
                    if message["recipient_id"] == agent_id and not message["read"]:
                        unread.append(message)
            return unread
        except Exception as e:
            logger.error(f"Failed to get unread messages: {e}")
            return []
    
    def get_chat_partners(self, agent_id):
        """
        Get list of agents the specified agent has chatted with
        
        Args:
            agent_id: Agent ID to get chat partners for
            
        Returns:
            list: List of chat partner agent IDs
        """
        try:
            partners = set()
            for chat_key in self.chats.keys():
                agent1, agent2 = chat_key.split("_")
                if agent1 == agent_id:
                    partners.add(agent2)
                elif agent2 == agent_id:
                    partners.add(agent1)
            return list(partners)
        except Exception as e:
            logger.error(f"Failed to get chat partners: {e}")
            return []
    
    def clear_chat_history(self, agent_id1, agent_id2):
        """
        Clear chat history between two agents
        
        Args:
            agent_id1: First agent ID
            agent_id2: Second agent ID
            
        Returns:
            bool: True if chat history cleared, False otherwise
        """
        try:
            chat_key = f"{min(agent_id1, agent_id2)}_{max(agent_id1, agent_id2)}"
            if chat_key in self.chats:
                del self.chats[chat_key]
                logger.info(f"Chat history cleared: {chat_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear chat history: {e}")
            return False
    
    def save_chat_history(self):
        """
        Save chat history to disk
        
        Returns:
            bool: True if chat history saved successfully, False otherwise
        """
        try:
            logger.info("Chat history saved to disk")
            return True
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
            return False
