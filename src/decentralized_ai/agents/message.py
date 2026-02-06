"""
Agent message data structures
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import time


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
