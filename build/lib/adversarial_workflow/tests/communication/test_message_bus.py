"""
Tests for MessageBus and related components.

This module contains comprehensive tests for the MessageBus routing system
used in the adversarial workflow for inter-agent communication.

Test Coverage:
- Agent registration and unregistration
- Message routing and delivery
- Error handling (unknown recipient, delivery failure)
- Message history tracking
- Concurrent operations
"""

import pytest

from adversarial_workflow.communication.message_bus import (
    AgentAlreadyRegisteredError,
    AgentNotRegisteredError,
    DeliveryFailureError,
    MessageBus,
    MessageRecord,
    UnknownRecipientError,
)
from adversarial_workflow.communication.messages import MessageEnvelope


class TestAgentRegistration:
    """Test cases for agent registration and lifecycle."""

    def test_register_agent(self) -> None:
        """Test successful agent registration."""
        bus = MessageBus()
        handler_called = []

        def handler(msg: MessageEnvelope) -> None:
            handler_called.append(msg)

        bus.register_agent("advocate", handler)
        assert bus.is_registered("advocate")
        assert "advocate" in bus.get_registered_agents()

    def test_register_multiple_agents(self) -> None:
        """Test registering multiple agents."""
        bus = MessageBus()

        def handler1(msg: MessageEnvelope) -> None:
            pass

        def handler2(msg: MessageEnvelope) -> None:
            pass

        def handler3(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("advocate", handler1)
        bus.register_agent("adversary", handler2)
        bus.register_agent("judge", handler3)

        assert bus.is_registered("advocate")
        assert bus.is_registered("adversary")
        assert bus.is_registered("judge")
        assert len(bus.get_registered_agents()) == 3

    def test_register_agent_empty_id(self) -> None:
        """Test that agent_id cannot be empty."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        with pytest.raises(ValueError, match="agent_id cannot be empty"):
            bus.register_agent("", handler)

    def test_register_agent_whitespace_id(self) -> None:
        """Test that agent_id cannot be whitespace only."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        with pytest.raises(ValueError, match="agent_id cannot be whitespace only"):
            bus.register_agent("   ", handler)

    def test_register_agent_invalid_id(self) -> None:
        """Test that agent_id must be valid agent identifier."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        with pytest.raises(ValueError, match="agent_id must be one of"):
            bus.register_agent("invalid_agent", handler)

    def test_register_agent_already_registered(self) -> None:
        """Test that registering same agent twice raises error."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("advocate", handler)

        with pytest.raises(AgentAlreadyRegisteredError):
            bus.register_agent("advocate", handler)

    def test_unregister_agent(self) -> None:
        """Test successful agent unregistration."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("advocate", handler)
        assert bus.is_registered("advocate")

        bus.unregister_agent("advocate")
        assert not bus.is_registered("advocate")
        assert "advocate" not in bus.get_registered_agents()

    def test_unregister_agent_not_registered(self) -> None:
        """Test unregistering non-registered agent raises error."""
        bus = MessageBus()

        with pytest.raises(AgentNotRegisteredError):
            bus.unregister_agent("advocate")

    def test_is_registered_false_for_unregistered(self) -> None:
        """Test is_registered returns False for unregistered agent."""
        bus = MessageBus()
        assert not bus.is_registered("advocate")

    def test_get_registered_agents_empty(self) -> None:
        """Test get_registered_agents returns empty list initially."""
        bus = MessageBus()
        assert bus.get_registered_agents() == []


class TestMessageDelivery:
    """Test cases for message routing and delivery."""

    def test_send_message_successful(self) -> None:
        """Test successful message delivery."""
        bus = MessageBus()
        received_messages: list[MessageEnvelope] = []

        def handler(msg: MessageEnvelope) -> None:
            received_messages.append(msg)

        bus.register_agent("judge", handler)

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        result = bus.send_message(message)
        assert result is True
        assert len(received_messages) == 1
        assert received_messages[0].message_id == message.message_id

    def test_send_message_to_unregistered_recipient(self) -> None:
        """Test sending message to unregistered recipient raises error."""
        bus = MessageBus()

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        with pytest.raises(UnknownRecipientError) as exc_info:
            bus.send_message(message)

        assert exc_info.value.agent_id == "judge"
        assert exc_info.value.message_id == message.message_id

    def test_send_message_delivery_failure(self) -> None:
        """Test delivery failure when handler raises exception."""
        bus = MessageBus()

        def failing_handler(msg: MessageEnvelope) -> None:
            raise RuntimeError("Handler failure")

        bus.register_agent("judge", failing_handler)

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        with pytest.raises(DeliveryFailureError) as exc_info:
            bus.send_message(message)

        assert exc_info.value.agent_id == "judge"
        assert exc_info.value.message_id == message.message_id
        assert "RuntimeError" in exc_info.value.reason

    def test_send_multiple_messages(self) -> None:
        """Test sending multiple messages to same recipient."""
        bus = MessageBus()
        received_messages: list[MessageEnvelope] = []

        def handler(msg: MessageEnvelope) -> None:
            received_messages.append(msg)

        bus.register_agent("judge", handler)

        message1 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze1"},
        )

        message2 = MessageEnvelope.create_request(
            sender="adversary",
            receiver="judge",
            payload={"action": "analyze2"},
        )

        bus.send_message(message1)
        bus.send_message(message2)

        assert len(received_messages) == 2
        assert received_messages[0].payload["action"] == "analyze1"
        assert received_messages[1].payload["action"] == "analyze2"

    def test_send_messages_to_different_recipients(self) -> None:
        """Test routing messages to different registered agents."""
        bus = MessageBus()
        advocate_messages: list[MessageEnvelope] = []
        judge_messages: list[MessageEnvelope] = []

        def advocate_handler(msg: MessageEnvelope) -> None:
            advocate_messages.append(msg)

        def judge_handler(msg: MessageEnvelope) -> None:
            judge_messages.append(msg)

        bus.register_agent("advocate", advocate_handler)
        bus.register_agent("judge", judge_handler)

        message_to_advocate = MessageEnvelope.create_request(
            sender="adversary",
            receiver="advocate",
            payload={"action": "respond"},
        )

        message_to_judge = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "synthesize"},
        )

        bus.send_message(message_to_advocate)
        bus.send_message(message_to_judge)

        assert len(advocate_messages) == 1
        assert len(judge_messages) == 1
        assert advocate_messages[0].payload["action"] == "respond"
        assert judge_messages[0].payload["action"] == "synthesize"


class TestMessageHistory:
    """Test cases for message history tracking."""

    def test_message_history_successful_delivery(self) -> None:
        """Test history records successful delivery."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("judge", handler)

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        bus.send_message(message)

        history = bus.get_message_history()
        assert len(history) == 1
        assert history[0].message.message_id == message.message_id
        assert history[0].delivered is True
        assert history[0].delivery_error is None

    def test_message_history_delivery_failure(self) -> None:
        """Test history records delivery failures."""
        bus = MessageBus()

        def failing_handler(msg: MessageEnvelope) -> None:
            raise ValueError("Test failure")

        bus.register_agent("judge", failing_handler)

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        with pytest.raises(DeliveryFailureError):
            bus.send_message(message)

        history = bus.get_message_history()
        assert len(history) == 1
        assert history[0].delivered is False
        assert history[0].delivery_error is not None
        assert "ValueError" in history[0].delivery_error

    def test_message_history_unknown_recipient(self) -> None:
        """Test history records unknown recipient errors."""
        bus = MessageBus()

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        with pytest.raises(UnknownRecipientError):
            bus.send_message(message)

        history = bus.get_message_history()
        assert len(history) == 1
        assert history[0].delivered is False
        assert history[0].delivery_error is not None
        assert "Unknown recipient" in history[0].delivery_error

    def test_get_message_history_filter_by_agent(self) -> None:
        """Test filtering message history by agent ID."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("judge", handler)
        bus.register_agent("advocate", handler)

        # Message involving advocate
        message1 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze1"},
        )

        # Message not involving advocate
        message2 = MessageEnvelope.create_request(
            sender="adversary",
            receiver="judge",
            payload={"action": "analyze2"},
        )

        bus.send_message(message1)
        bus.send_message(message2)

        # Filter by advocate (should get message1 only)
        advocate_history = bus.get_message_history(agent_id="advocate")
        assert len(advocate_history) == 1
        assert advocate_history[0].message.message_id == message1.message_id

    def test_get_message_history_filter_by_message_type(self) -> None:
        """Test filtering message history by message type."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("judge", handler)
        bus.register_agent("advocate", handler)

        # Create request message
        request_msg = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        # Create response message
        response_msg = MessageEnvelope.create_response(
            sender="judge",
            receiver="advocate",
            payload={"result": "complete"},
            correlation_id="test-123",
        )

        bus.send_message(request_msg)
        bus.send_message(response_msg)

        # Filter by request type
        request_history = bus.get_message_history(message_type="request")
        assert len(request_history) == 1
        assert request_history[0].message.message_type == "request"

        # Filter by response type
        response_history = bus.get_message_history(message_type="response")
        assert len(response_history) == 1
        assert response_history[0].message.message_type == "response"

    def test_get_message_history_combined_filters(self) -> None:
        """Test filtering message history by both agent and type."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("judge", handler)
        bus.register_agent("advocate", handler)

        # advocate sends request to judge
        message1 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze1"},
        )

        # adversary sends request to judge
        message2 = MessageEnvelope.create_request(
            sender="adversary",
            receiver="judge",
            payload={"action": "analyze2"},
        )

        # judge sends response to advocate
        message3 = MessageEnvelope.create_response(
            sender="judge",
            receiver="advocate",
            payload={"result": "complete"},
            correlation_id="test-123",
        )

        bus.send_message(message1)
        bus.send_message(message2)
        bus.send_message(message3)

        # Filter by advocate + request type
        filtered = bus.get_message_history(agent_id="advocate", message_type="request")
        assert len(filtered) == 1
        assert filtered[0].message.message_id == message1.message_id

    def test_clear_history(self) -> None:
        """Test clearing message history."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("judge", handler)

        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        bus.send_message(message)
        assert bus.get_history_count() == 1

        bus.clear_history()
        assert bus.get_history_count() == 0
        assert bus.get_message_history() == []

    def test_get_history_count(self) -> None:
        """Test getting message history count."""
        bus = MessageBus()

        def handler(msg: MessageEnvelope) -> None:
            pass

        bus.register_agent("judge", handler)

        assert bus.get_history_count() == 0

        message1 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze1"},
        )

        message2 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze2"},
        )

        bus.send_message(message1)
        assert bus.get_history_count() == 1

        bus.send_message(message2)
        assert bus.get_history_count() == 2


class TestMessageRecord:
    """Test cases for MessageRecord dataclass."""

    def test_message_record_to_dict(self) -> None:
        """Test converting MessageRecord to dictionary."""
        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        record = MessageRecord(
            message=message,
            delivered=True,
            delivery_error=None,
        )

        result = record.to_dict()
        assert result["delivered"] is True
        assert result["delivery_error"] is None
        assert result["message"]["sender"] == "advocate"
        assert result["message"]["receiver"] == "judge"

    def test_message_record_with_error(self) -> None:
        """Test MessageRecord with delivery error."""
        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "analyze"},
        )

        record = MessageRecord(
            message=message,
            delivered=False,
            delivery_error="Test error message",
        )

        assert record.delivered is False
        assert record.delivery_error == "Test error message"

        result = record.to_dict()
        assert result["delivered"] is False
        assert result["delivery_error"] == "Test error message"
