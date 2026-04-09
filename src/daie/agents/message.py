"""
Agent message data structures
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentMessage:
    """Structure for agent messages"""

    id: str = field(default_factory=lambda: str(time.time_ns()))
    sender_id: str = ""
    receiver_id: str = ""
    content: str = ""
    message_type: str = "text"
    timestamp: float = field(default_factory=time.time)
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_data: str) -> "AgentMessage":
        """Create message from JSON string"""
        data = json.loads(json_data)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
            "images": self.images,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary"""
        return cls(
            id=data.get("id", str(time.time_ns())),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            content=data.get("content", ""),
            message_type=data.get("message_type", "text"),
            timestamp=data.get("timestamp", time.time()),
            images=data.get("images", []),
            metadata=data.get("metadata", {}),
        )
