"""
Message queue manager for OpenClaw Telegram Bridge.
Handles saving and loading messages from JSON storage.

This module is compatible with the format used by bridge.py.
"""
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict

from config import QUEUE_FILE


class MessageType(Enum):
    """Types of messages in the queue."""
    TASK = "task"
    QUESTION = "question"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    QUESTION_FROM_KIMI = "question_from_kimi"


class MessageStatus(Enum):
    """Status of a message in the queue."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Message:
    """
    Represents a message in the queue.
    Compatible with the bridge.py format.
    """
    id: str
    type: str
    from_user: str
    content: str
    timestamp: str
    status: str
    metadata: dict
    
    @classmethod
    def create(
        cls,
        msg_type: MessageType,
        from_user: str,
        content: str,
        metadata: dict = None
    ) -> "Message":
        """Create a new message with auto-generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            type=msg_type.value,
            from_user=from_user,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=MessageStatus.PENDING.value,
            metadata=metadata or {}
        )
    
    def to_dict(self) -> dict:
        """Convert message to dictionary (bridge.py compatible format)."""
        return {
            "id": self.id,
            "type": self.type,
            "from": self.from_user,
            "content": self.content,
            "timestamp": self.timestamp,
            "status": self.status,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create message from dictionary (bridge.py compatible format)."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            from_user=data.get("from", "unknown"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            status=data.get("status", MessageStatus.PENDING.value),
            metadata=data.get("metadata", {})
        )


class QueueManager:
    """
    Manages the message queue stored in a JSON file.
    Compatible with the bridge.py format (simple list).
    """
    
    def __init__(self, queue_file: Path = QUEUE_FILE):
        self.queue_file = queue_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Create queue file if it doesn't exist."""
        if not self.queue_file.exists():
            self._save_data([])
    
    def _load_data(self) -> list:
        """Load queue data from file (returns list)."""
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both list format (bridge.py) and dict format (legacy)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "messages" in data:
                    return data["messages"]
                else:
                    return []
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_data(self, data: list) -> None:
        """Save queue data to file (expects list)."""
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_message(
        self,
        msg_type: MessageType,
        from_user: str,
        content: str,
        metadata: dict = None
    ) -> Message:
        """
        Add a new message to the queue.
        
        Args:
            msg_type: Type of message (task, question, etc.)
            from_user: Who sent the message (user/kimi)
            content: Message content
            metadata: Optional additional data
            
        Returns:
            The created Message object
        """
        message = Message.create(msg_type, from_user, content, metadata)
        
        data = self._load_data()
        data.append(message.to_dict())
        self._save_data(data)
        
        return message
    
    def get_pending_messages(self) -> list[Message]:
        """Get all pending messages."""
        data = self._load_data()
        return [
            Message.from_dict(m)
            for m in data
            if m.get("status") == MessageStatus.PENDING.value
        ]
    
    def get_messages_by_type(self, msg_type: MessageType) -> list[Message]:
        """Get all messages of a specific type."""
        data = self._load_data()
        return [
            Message.from_dict(m)
            for m in data
            if m.get("type") == msg_type.value
        ]
    
    def update_message_status(
        self,
        message_id: str,
        status: MessageStatus
    ) -> bool:
        """
        Update the status of a message.
        
        Args:
            message_id: UUID of the message
            status: New status
            
        Returns:
            True if message was found and updated, False otherwise
        """
        data = self._load_data()
        
        for msg in data:
            if msg.get("id") == message_id:
                msg["status"] = status.value
                self._save_data(data)
                return True
        
        return False
    
    def get_queue_status(self) -> dict:
        """
        Get current queue status summary.
        
        Returns:
            Dictionary with queue statistics
        """
        data = self._load_data()
        
        pending = sum(1 for m in data if m.get("status") == MessageStatus.PENDING.value)
        processing = sum(1 for m in data if m.get("status") == MessageStatus.PROCESSING.value)
        completed = sum(1 for m in data if m.get("status") == MessageStatus.COMPLETED.value)
        failed = sum(1 for m in data if m.get("status") == MessageStatus.FAILED.value)
        
        return {
            "total": len(data),
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed
        }
    
    def clear_completed(self) -> int:
        """
        Remove completed and failed messages from queue.
        
        Returns:
            Number of messages removed
        """
        data = self._load_data()
        original_count = len(data)
        
        data = [
            m for m in data
            if m.get("status") not in (MessageStatus.COMPLETED.value, MessageStatus.FAILED.value)
        ]
        
        removed = original_count - len(data)
        self._save_data(data)
        
        return removed
