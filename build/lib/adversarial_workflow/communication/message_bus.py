"""
Message bus for adversarial workflow agent communication.

This module implements the central message routing and delivery system for
inter-agent communication in the three-agent adversarial workflow system.

Components:
- MessageBus: Central routing hub for agent messages
- Agent registration and lifecycle management
- Message delivery with error handling
- Message tracking and history
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .messages import MessageEnvelope

logger = logging.getLogger(__name__)


class MessageBusError(Exception):
    """Base exception for message bus errors."""

    pass


class UnknownRecipientError(MessageBusError):
    """Raised when message recipient is not registered."""

    def __init__(self, agent_id: str, message_id: str) -> None:
        self.agent_id = agent_id
        self.message_id = message_id
        super().__init__(f"Unknown recipient '{agent_id}' for message '{message_id}'")


class DeliveryFailureError(MessageBusError):
    """Raised when message delivery fails."""

    def __init__(self, agent_id: str, message_id: str, reason: str) -> None:
        self.agent_id = agent_id
        self.message_id = message_id
        self.reason = reason
        super().__init__(f"Failed to deliver message '{message_id}' to '{agent_id}': {reason}")


class AgentAlreadyRegisteredError(MessageBusError):
    """Raised when attempting to register an already registered agent."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' is already registered")


class AgentNotRegisteredError(MessageBusError):
    """Raised when attempting operations on unregistered agent."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' is not registered")


@dataclass
class MessageRecord:
    """Record of a message in the message bus history."""

    message: MessageEnvelope
    delivered: bool
    delivery_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "message": self.message.to_dict(),
            "delivered": self.delivered,
            "delivery_error": self.delivery_error,
        }


class MessageBus:
    """
    Central message routing and delivery system.

    The MessageBus manages agent registration and routes messages between
    registered agents in the adversarial workflow system.

    Attributes:
        _agents: Dictionary mapping agent IDs to message handler callbacks
        _message_history: List of all messages processed by the bus
    """

    def __init__(self) -> None:
        """Initialize message bus with empty agent registry and history."""
        self._agents: dict[str, Callable[[MessageEnvelope], None]] = {}
        self._message_history: list[MessageRecord] = []
        logger.info("MessageBus initialized")

    def register_agent(
        self, agent_id: str, message_handler: Callable[[MessageEnvelope], None]
    ) -> None:
        """
        Register an agent with the message bus.

        Args:
            agent_id: Unique identifier for the agent
            message_handler: Callback function to handle incoming messages

        Raises:
            ValueError: If agent_id is empty or whitespace only
            AgentAlreadyRegisteredError: If agent is already registered
        """
        if not agent_id:
            raise ValueError("agent_id cannot be empty")

        if not agent_id.strip():
            raise ValueError("agent_id cannot be whitespace only")

        valid_agents = ["advocate", "adversary", "judge"]
        if agent_id not in valid_agents:
            raise ValueError(f"agent_id must be one of {valid_agents}, got '{agent_id}'")

        if agent_id in self._agents:
            raise AgentAlreadyRegisteredError(agent_id)

        self._agents[agent_id] = message_handler
        logger.info(f"Agent '{agent_id}' registered with message bus")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the message bus.

        Args:
            agent_id: Identifier of agent to unregister

        Raises:
            AgentNotRegisteredError: If agent is not currently registered
        """
        if agent_id not in self._agents:
            raise AgentNotRegisteredError(agent_id)

        del self._agents[agent_id]
        logger.info(f"Agent '{agent_id}' unregistered from message bus")

    def is_registered(self, agent_id: str) -> bool:
        """
        Check if an agent is currently registered.

        Args:
            agent_id: Agent identifier to check

        Returns:
            True if agent is registered, False otherwise
        """
        return agent_id in self._agents

    def get_registered_agents(self) -> list[str]:
        """
        Get list of currently registered agent IDs.

        Returns:
            List of registered agent identifiers
        """
        return list(self._agents.keys())

    def send_message(self, message: MessageEnvelope) -> bool:
        """
        Route and deliver message to recipient agent.

        Args:
            message: MessageEnvelope to deliver

        Returns:
            True if message was delivered successfully

        Raises:
            UnknownRecipientError: If recipient is not registered
            DeliveryFailureError: If message delivery fails
        """
        # Validate recipient is registered
        if message.receiver not in self._agents:
            error = UnknownRecipientError(message.receiver, message.message_id)
            self._record_message(message, delivered=False, error=str(error))
            raise error

        # Attempt delivery
        try:
            handler = self._agents[message.receiver]
            handler(message)
            self._record_message(message, delivered=True)
            logger.info(f"Message '{message.message_id}' delivered to '{message.receiver}'")
            return True

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self._record_message(message, delivered=False, error=error_msg)
            raise DeliveryFailureError(message.receiver, message.message_id, error_msg) from e

    def get_message_history(
        self, agent_id: str | None = None, message_type: str | None = None
    ) -> list[MessageRecord]:
        """
        Retrieve message history with optional filtering.

        Args:
            agent_id: Filter by sender or receiver (optional)
            message_type: Filter by message type (optional)

        Returns:
            List of MessageRecord objects matching filters
        """
        history = self._message_history

        if agent_id is not None:
            history = [
                record
                for record in history
                if record.message.sender == agent_id or record.message.receiver == agent_id
            ]

        if message_type is not None:
            history = [record for record in history if record.message.message_type == message_type]

        return history

    def clear_history(self) -> None:
        """Clear all message history."""
        self._message_history.clear()
        logger.info("Message history cleared")

    def get_history_count(self) -> int:
        """
        Get total count of messages in history.

        Returns:
            Number of messages processed
        """
        return len(self._message_history)

    def _record_message(
        self, message: MessageEnvelope, delivered: bool, error: str | None = None
    ) -> None:
        """
        Record message in history.

        Args:
            message: The message to record
            delivered: Whether delivery was successful
            error: Optional error message if delivery failed
        """
        record = MessageRecord(message=message, delivered=delivered, delivery_error=error)
        self._message_history.append(record)
