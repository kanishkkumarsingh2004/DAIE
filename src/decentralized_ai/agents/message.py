"""
Agent message data structures
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import time
import json


@dataclass
class AgentMessage:
    """Structure for agent messages"""
    id: str = field(default_factory=lambda: str(time.time_ns()))
    sender_id: str = ""
    receiver_id: str = ""
    content: str = ""
    message_type: str = "text"
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps({
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        })
    
    @classmethod
    def from_json(cls, json_data: str) -> 'AgentMessage':
        """Create message from JSON string"""
        data = json.loads(json_data)
        return cls(
            id=data.get("id", str(time.time_ns())),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            content=data.get("content", ""),
            message_type=data.get("message_type", "text"),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )
