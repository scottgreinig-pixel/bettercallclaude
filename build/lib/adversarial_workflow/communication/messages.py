"""
Message schemas for adversarial workflow agent communication.

This module defines the message envelope and message types for inter-agent
communication in the three-agent adversarial workflow system.

Message Types:
- request: Agent requesting action/analysis from another agent
- response: Agent responding to a request
- event: Notification of state change or completion

YAML Schema:
    message_id: str (unique identifier)
    sender: str (agent identifier: "advocate" | "adversary" | "judge")
    receiver: str (agent identifier: "advocate" | "adversary" | "judge")
    message_type: "request" | "response" | "event"
    timestamp: float (Unix timestamp)
    payload: Dict[str, Any] (message-specific content)
    correlation_id: Optional[str] (for tracking request-response pairs)
"""

import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal

import yaml


@dataclass
class MessageEnvelope:
    """
    Message envelope for inter-agent communication.

    Attributes:
        message_id: Unique message identifier (UUID)
        sender: Sending agent identifier
        receiver: Receiving agent identifier
        message_type: Type of message (request, response, event)
        timestamp: Unix timestamp of message creation
        payload: Message-specific content
        correlation_id: Optional ID linking requests to responses
    """

    message_id: str
    sender: str
    receiver: str
    message_type: Literal["request", "response", "event"]
    timestamp: float
    payload: dict[str, Any]
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        """Validate message envelope after initialization."""
        # Validate message_id
        if not self.message_id:
            raise ValueError("message_id cannot be empty")

        if not self.message_id.strip():
            raise ValueError("message_id cannot be whitespace only")

        # Validate sender
        if not self.sender:
            raise ValueError("sender cannot be empty")

        if not self.sender.strip():
            raise ValueError("sender cannot be whitespace only")

        valid_agents = ["advocate", "adversary", "judge"]
        if self.sender not in valid_agents:
            raise ValueError(f"sender must be one of {valid_agents}, got '{self.sender}'")

        # Validate receiver
        if not self.receiver:
            raise ValueError("receiver cannot be empty")

        if not self.receiver.strip():
            raise ValueError("receiver cannot be whitespace only")

        if self.receiver not in valid_agents:
            raise ValueError(f"receiver must be one of {valid_agents}, got '{self.receiver}'")

        # Validate timestamp
        if self.timestamp < 0:
            raise ValueError(f"timestamp must be non-negative, got {self.timestamp}")

        # Validate correlation_id if provided
        if self.correlation_id is not None:
            if not self.correlation_id.strip():
                raise ValueError("correlation_id cannot be whitespace only")

    def to_dict(self) -> dict[str, Any]:
        """Convert message envelope to dictionary for YAML serialization."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageEnvelope":
        """Create MessageEnvelope from dictionary."""
        return cls(
            message_id=data["message_id"],
            sender=data["sender"],
            receiver=data["receiver"],
            message_type=data["message_type"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
        )

    def to_yaml(self) -> str:
        """Convert message envelope to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "MessageEnvelope":
        """Create MessageEnvelope from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    @staticmethod
    def create_request(
        sender: str,
        receiver: str,
        payload: dict[str, Any],
    ) -> "MessageEnvelope":
        """
        Create a request message.

        Args:
            sender: Sending agent identifier
            receiver: Receiving agent identifier
            payload: Request-specific content

        Returns:
            MessageEnvelope with type="request"
        """
        return MessageEnvelope(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            message_type="request",
            timestamp=time.time(),
            payload=payload,
            correlation_id=None,
        )

    @staticmethod
    def create_response(
        sender: str,
        receiver: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> "MessageEnvelope":
        """
        Create a response message.

        Args:
            sender: Sending agent identifier
            receiver: Receiving agent identifier
            payload: Response-specific content
            correlation_id: ID of the request being responded to

        Returns:
            MessageEnvelope with type="response"
        """
        return MessageEnvelope(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            message_type="response",
            timestamp=time.time(),
            payload=payload,
            correlation_id=correlation_id,
        )

    @staticmethod
    def create_event(
        sender: str,
        receiver: str,
        payload: dict[str, Any],
    ) -> "MessageEnvelope":
        """
        Create an event message.

        Args:
            sender: Sending agent identifier
            receiver: Receiving agent identifier
            payload: Event-specific content

        Returns:
            MessageEnvelope with type="event"
        """
        return MessageEnvelope(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            message_type="event",
            timestamp=time.time(),
            payload=payload,
            correlation_id=None,
        )
