"""
Agent Node System - Working Memory
Decentralized AI Ecosystem

This module manages the working memory for the agent. Working memory
stores information about current tasks, conversations, and context that
the agent is actively working with.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WorkingMemory:
    """
    Working memory stores current task and conversation information
    
    This class manages:
    - Current active tasks
    - Conversation history (short-term)
    - Context information for ongoing operations
    - Temporary storage for task results
    """
    
    def __init__(self):
        """Initialize working memory"""
        self.tasks = {}  # task_id: task_info
        self.conversations = {}  # conversation_id: conversation_info
        self.context = {}  # context_type: context_info
        self.temporary_storage = {}  # key: value
        self.last_cleanup = datetime.now()
        
        logger.info("Working memory initialized")
    
    # Task management methods
    def add_task(self, task_id: str, task_info: Dict[str, Any]) -> bool:
        """
        Add a new task to working memory
        
        Args:
            task_id: Unique task identifier
            task_info: Dictionary containing task information
            
        Returns:
            True if task added successfully, False if already exists
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists in working memory")
            return False
        
        self.tasks[task_id] = {
            **task_info,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "active"
        }
        
        logger.info(f"Task {task_id} added to working memory")
        return True
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get task information from working memory
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Task information dictionary or None if not found
        """
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update task information
        
        Args:
            task_id: Unique task identifier
            updates: Dictionary containing updates
            
        Returns:
            True if task updated successfully, False if not found
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found in working memory")
            return False
        
        self.tasks[task_id].update({
            **updates,
            "updated_at": datetime.now()
        })
        
        logger.debug(f"Task {task_id} updated")
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from working memory
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            True if task removed successfully, False if not found
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found in working memory")
            return False
        
        del self.tasks[task_id]
        logger.info(f"Task {task_id} removed from working memory")
        return True
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all active tasks
        
        Returns:
            List of active task information dictionaries
        """
        return [task for task in self.tasks.values() if task["status"] == "active"]
    
    # Conversation management methods
    def add_conversation(self, conversation_id: str, conversation_info: Dict[str, Any]) -> bool:
        """
        Add a new conversation to working memory
        
        Args:
            conversation_id: Unique conversation identifier
            conversation_info: Dictionary containing conversation information
            
        Returns:
            True if conversation added successfully, False if already exists
        """
        if conversation_id in self.conversations:
            logger.warning(f"Conversation {conversation_id} already exists in working memory")
            return False
        
        self.conversations[conversation_id] = {
            **conversation_info,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": []
        }
        
        logger.info(f"Conversation {conversation_id} added to working memory")
        return True
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation information from working memory
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Conversation information dictionary or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: Unique conversation identifier
            message: Dictionary containing message information
            
        Returns:
            True if message added successfully, False if conversation not found
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found in working memory")
            return False
        
        self.conversations[conversation_id]["messages"].append({
            **message,
            "timestamp": datetime.now()
        })
        
        self.conversations[conversation_id]["updated_at"] = datetime.now()
        
        logger.debug(f"Message added to conversation {conversation_id}")
        return True
    
    def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update conversation information
        
        Args:
            conversation_id: Unique conversation identifier
            updates: Dictionary containing updates
            
        Returns:
            True if conversation updated successfully, False if not found
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found in working memory")
            return False
        
        self.conversations[conversation_id].update({
            **updates,
            "updated_at": datetime.now()
        })
        
        logger.debug(f"Conversation {conversation_id} updated")
        return True
    
    def remove_conversation(self, conversation_id: str) -> bool:
        """
        Remove a conversation from working memory
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            True if conversation removed successfully, False if not found
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found in working memory")
            return False
        
        del self.conversations[conversation_id]
        logger.info(f"Conversation {conversation_id} removed from working memory")
        return True
    
    # Context management methods
    def set_context(self, context_type: str, context_info: Dict[str, Any]) -> None:
        """
        Set context information
        
        Args:
            context_type: Type of context
            context_info: Dictionary containing context information
        """
        self.context[context_type] = {
            **context_info,
            "updated_at": datetime.now()
        }
        
        logger.debug(f"Context {context_type} updated")
    
    def get_context(self, context_type: str) -> Dict[str, Any]:
        """
        Get context information
        
        Args:
            context_type: Type of context
            
        Returns:
            Context information dictionary or empty dict if not found
        """
        return self.context.get(context_type, {})
    
    def remove_context(self, context_type: str) -> None:
        """
        Remove context information
        
        Args:
            context_type: Type of context to remove
        """
        if context_type in self.context:
            del self.context[context_type]
            logger.debug(f"Context {context_type} removed")
    
    # Temporary storage methods
    def set_temporary(self, key: str, value: Any) -> None:
        """
        Store temporary data
        
        Args:
            key: Key to store value under
            value: Value to store
        """
        self.temporary_storage[key] = {
            "value": value,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        logger.debug(f"Temporary data '{key}' stored")
    
    def get_temporary(self, key: str, default: Any = None) -> Any:
        """
        Get temporary data
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        item = self.temporary_storage.get(key)
        return item["value"] if item else default
    
    def remove_temporary(self, key: str) -> bool:
        """
        Remove temporary data
        
        Args:
            key: Key to remove
            
        Returns:
            True if key existed and was removed, False otherwise
        """
        if key in self.temporary_storage:
            del self.temporary_storage[key]
            logger.debug(f"Temporary data '{key}' removed")
            return True
        
        return False
    
    # Cleanup and maintenance methods
    async def cleanup(self, max_age: int = 3600) -> int:
        """
        Clean up old items from working memory
        
        Args:
            max_age: Maximum age in seconds for items to retain
            
        Returns:
            Number of items removed
        """
        removed_count = 0
        cutoff_time = datetime.now() - timedelta(seconds=max_age)
        
        logger.debug("Starting working memory cleanup...")
        
        # Cleanup tasks
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task["updated_at"] < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self.remove_task(task_id)
            removed_count += 1
        
        # Cleanup conversations
        conversations_to_remove = []
        for conversation_id, conversation in self.conversations.items():
            if conversation["updated_at"] < cutoff_time:
                conversations_to_remove.append(conversation_id)
        
        for conversation_id in conversations_to_remove:
            self.remove_conversation(conversation_id)
            removed_count += 1
        
        # Cleanup temporary storage
        temp_to_remove = []
        for key, item in self.temporary_storage.items():
            if item["updated_at"] < cutoff_time:
                temp_to_remove.append(key)
        
        for key in temp_to_remove:
            self.remove_temporary(key)
            removed_count += 1
        
        # Cleanup old context
        context_to_remove = []
        for context_type, context in self.context.items():
            if context["updated_at"] < cutoff_time:
                context_to_remove.append(context_type)
        
        for context_type in context_to_remove:
            self.remove_context(context_type)
            removed_count += 1
        
        self.last_cleanup = datetime.now()
        
        logger.debug(f"Working memory cleanup completed. Removed {removed_count} items")
        
        return removed_count
    
    def clear(self) -> None:
        """Clear all working memory"""
        logger.warning("Clearing all working memory")
        
        self.tasks.clear()
        self.conversations.clear()
        self.context.clear()
        self.temporary_storage.clear()
        self.last_cleanup = datetime.now()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get working memory statistics
        
        Returns:
            Dictionary containing working memory statistics
        """
        return {
            "tasks": len(self.tasks),
            "active_tasks": len([t for t in self.tasks.values() if t["status"] == "active"]),
            "conversations": len(self.conversations),
            "messages": sum(len(c["messages"]) for c in self.conversations.values()),
            "context_entries": len(self.context),
            "temporary_items": len(self.temporary_storage),
            "last_cleanup": int((datetime.now() - self.last_cleanup).total_seconds())
        }
    
    def debug_info(self) -> Dict[str, Any]:
        """
        Get detailed debug information
        
        Returns:
            Dictionary containing detailed working memory information
        """
        stats = self.get_stats()
        return {
            "stats": stats,
            "tasks": list(self.tasks.keys()),
            "conversations": list(self.conversations.keys()),
            "context_types": list(self.context.keys()),
            "temporary_keys": list(self.temporary_storage.keys())
        }
    
    def save_state(self) -> Dict[str, Any]:
        """
        Save working memory state
        
        Returns:
            Dictionary containing working memory state
        """
        state = {
            "tasks": self.tasks,
            "conversations": self.conversations,
            "context": self.context,
            "temporary_storage": {k: {"value": v["value"], "created_at": str(v["created_at"]), "updated_at": str(v["updated_at"])} for k, v in self.temporary_storage.items()},
            "last_cleanup": str(self.last_cleanup)
        }
        
        return state
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Load working memory state
        
        Args:
            state: Dictionary containing working memory state
        """
        logger.info("Loading working memory state")
        
        self.tasks = state.get("tasks", {})
        self.conversations = state.get("conversations", {})
        self.context = state.get("context", {})
        self.temporary_storage = state.get("temporary_storage", {})
        
        if "last_cleanup" in state:
            try:
                self.last_cleanup = datetime.fromisoformat(state["last_cleanup"].replace("Z", "+00:00"))
            except:
                self.last_cleanup = datetime.now()
        
        logger.info("Working memory state loaded")
