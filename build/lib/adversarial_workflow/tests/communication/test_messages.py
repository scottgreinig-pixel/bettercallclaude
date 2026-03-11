"""
Tests for MessageEnvelope data structure.

This module contains comprehensive tests for the MessageEnvelope schema
used in the adversarial workflow system for agent communication.

Test Coverage:
- Message creation validation (required fields, format)
- Agent identifier validation (valid agents only)
- Timestamp validation (non-negative)
- Correlation ID validation (optional, non-empty)
- YAML serialization/deserialization
- Factory methods (create_request, create_response, create_event)
"""

import time

import pytest

from adversarial_workflow.communication.messages import MessageEnvelope


class TestMessageEnvelopeValidation:
    """Test cases for MessageEnvelope validation."""

    def test_valid_message_creation(self) -> None:
        """Test creating a valid message envelope."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="advocate",
            receiver="judge",
            message_type="request",
            timestamp=time.time(),
            payload={"action": "analyze_case"},
            correlation_id=None,
        )
        assert message.message_id == "test-123"
        assert message.sender == "advocate"
        assert message.receiver == "judge"
        assert message.message_type == "request"

    def test_message_id_required(self) -> None:
        """Test that message_id cannot be empty."""
        with pytest.raises(ValueError, match="message_id cannot be empty"):
            MessageEnvelope(
                message_id="",
                sender="advocate",
                receiver="judge",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_message_id_whitespace_only(self) -> None:
        """Test that message_id cannot be whitespace only."""
        with pytest.raises(ValueError, match="message_id cannot be whitespace only"):
            MessageEnvelope(
                message_id="   ",
                sender="advocate",
                receiver="judge",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_sender_required(self) -> None:
        """Test that sender cannot be empty."""
        with pytest.raises(ValueError, match="sender cannot be empty"):
            MessageEnvelope(
                message_id="test-123",
                sender="",
                receiver="judge",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_sender_whitespace_only(self) -> None:
        """Test that sender cannot be whitespace only."""
        with pytest.raises(ValueError, match="sender cannot be whitespace only"):
            MessageEnvelope(
                message_id="test-123",
                sender="   ",
                receiver="judge",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_sender_valid_agent(self) -> None:
        """Test that sender must be a valid agent identifier."""
        with pytest.raises(ValueError, match="sender must be one of"):
            MessageEnvelope(
                message_id="test-123",
                sender="invalid_agent",
                receiver="judge",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_receiver_required(self) -> None:
        """Test that receiver cannot be empty."""
        with pytest.raises(ValueError, match="receiver cannot be empty"):
            MessageEnvelope(
                message_id="test-123",
                sender="advocate",
                receiver="",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_receiver_whitespace_only(self) -> None:
        """Test that receiver cannot be whitespace only."""
        with pytest.raises(ValueError, match="receiver cannot be whitespace only"):
            MessageEnvelope(
                message_id="test-123",
                sender="advocate",
                receiver="   ",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_receiver_valid_agent(self) -> None:
        """Test that receiver must be a valid agent identifier."""
        with pytest.raises(ValueError, match="receiver must be one of"):
            MessageEnvelope(
                message_id="test-123",
                sender="advocate",
                receiver="invalid_agent",
                message_type="request",
                timestamp=time.time(),
                payload={},
            )

    def test_timestamp_non_negative(self) -> None:
        """Test that timestamp cannot be negative."""
        with pytest.raises(ValueError, match="timestamp must be non-negative"):
            MessageEnvelope(
                message_id="test-123",
                sender="advocate",
                receiver="judge",
                message_type="request",
                timestamp=-1.0,
                payload={},
            )

    def test_timestamp_zero_allowed(self) -> None:
        """Test that timestamp can be zero."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="advocate",
            receiver="judge",
            message_type="request",
            timestamp=0.0,
            payload={},
        )
        assert message.timestamp == 0.0

    def test_correlation_id_optional(self) -> None:
        """Test that correlation_id is optional."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="advocate",
            receiver="judge",
            message_type="request",
            timestamp=time.time(),
            payload={},
            correlation_id=None,
        )
        assert message.correlation_id is None

    def test_correlation_id_whitespace_only(self) -> None:
        """Test that correlation_id cannot be whitespace only if provided."""
        with pytest.raises(ValueError, match="correlation_id cannot be whitespace only"):
            MessageEnvelope(
                message_id="test-123",
                sender="advocate",
                receiver="judge",
                message_type="response",
                timestamp=time.time(),
                payload={},
                correlation_id="   ",
            )


class TestMessageTypes:
    """Test cases for different message types."""

    def test_request_message_type(self) -> None:
        """Test creating a request message."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="advocate",
            receiver="adversary",
            message_type="request",
            timestamp=time.time(),
            payload={"action": "analyze"},
        )
        assert message.message_type == "request"

    def test_response_message_type(self) -> None:
        """Test creating a response message."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="adversary",
            receiver="advocate",
            message_type="response",
            timestamp=time.time(),
            payload={"result": "complete"},
            correlation_id="original-request-id",
        )
        assert message.message_type == "response"
        assert message.correlation_id == "original-request-id"

    def test_event_message_type(self) -> None:
        """Test creating an event message."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="judge",
            receiver="advocate",
            message_type="event",
            timestamp=time.time(),
            payload={"event": "synthesis_complete"},
        )
        assert message.message_type == "event"


class TestMessageEnvelopeSerialization:
    """Test YAML serialization/deserialization for MessageEnvelope."""

    def test_to_dict(self) -> None:
        """Test converting MessageEnvelope to dictionary."""
        message = MessageEnvelope(
            message_id="test-123",
            sender="advocate",
            receiver="judge",
            message_type="request",
            timestamp=1234567890.0,
            payload={"action": "analyze", "case_id": "case-001"},
            correlation_id=None,
        )

        result = message.to_dict()
        assert result["message_id"] == "test-123"
        assert result["sender"] == "advocate"
        assert result["receiver"] == "judge"
        assert result["message_type"] == "request"
        assert result["timestamp"] == 1234567890.0
        assert result["payload"]["action"] == "analyze"
        assert result["correlation_id"] is None

    def test_from_dict(self) -> None:
        """Test creating MessageEnvelope from dictionary."""
        data = {
            "message_id": "test-456",
            "sender": "adversary",
            "receiver": "judge",
            "message_type": "response",
            "timestamp": 1234567890.0,
            "payload": {"result": "analysis_complete"},
            "correlation_id": "request-123",
        }

        message = MessageEnvelope.from_dict(data)
        assert message.message_id == "test-456"
        assert message.sender == "adversary"
        assert message.receiver == "judge"
        assert message.message_type == "response"
        assert message.correlation_id == "request-123"

    def test_to_yaml(self) -> None:
        """Test converting MessageEnvelope to YAML string."""
        message = MessageEnvelope(
            message_id="test-789",
            sender="judge",
            receiver="advocate",
            message_type="event",
            timestamp=1234567890.0,
            payload={"event": "synthesis_ready"},
            correlation_id=None,
        )

        yaml_str = message.to_yaml()
        assert isinstance(yaml_str, str)
        assert "message_id: test-789" in yaml_str
        assert "sender: judge" in yaml_str
        assert "message_type: event" in yaml_str

    def test_from_yaml(self) -> None:
        """Test creating MessageEnvelope from YAML string."""
        yaml_str = """
message_id: test-999
sender: advocate
receiver: adversary
message_type: request
timestamp: 1234567890.0
payload:
  action: analyze_position
  case_id: case-002
correlation_id: null
"""

        message = MessageEnvelope.from_yaml(yaml_str)
        assert message.message_id == "test-999"
        assert message.sender == "advocate"
        assert message.receiver == "adversary"
        assert message.payload["action"] == "analyze_position"

    def test_round_trip_serialization(self) -> None:
        """Test round-trip YAML serialization maintains data integrity."""
        original = MessageEnvelope(
            message_id="round-trip-test",
            sender="judge",
            receiver="advocate",
            message_type="response",
            timestamp=9876543210.0,
            payload={
                "synthesis": "balanced analysis",
                "risk_score": 0.75,
                "recommendations": ["action1", "action2"],
            },
            correlation_id="original-request",
        )

        # Convert to YAML and back
        yaml_str = original.to_yaml()
        restored = MessageEnvelope.from_yaml(yaml_str)

        # Verify all data preserved
        assert restored.message_id == original.message_id
        assert restored.sender == original.sender
        assert restored.receiver == original.receiver
        assert restored.message_type == original.message_type
        assert restored.timestamp == original.timestamp
        assert restored.correlation_id == original.correlation_id
        assert restored.payload == original.payload


class TestFactoryMethods:
    """Test factory methods for creating messages."""

    def test_create_request(self) -> None:
        """Test create_request factory method."""
        message = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={"action": "request_synthesis"},
        )

        assert message.message_type == "request"
        assert message.sender == "advocate"
        assert message.receiver == "judge"
        assert message.correlation_id is None
        assert len(message.message_id) > 0  # UUID generated
        assert message.timestamp > 0  # Current timestamp

    def test_create_response(self) -> None:
        """Test create_response factory method."""
        message = MessageEnvelope.create_response(
            sender="judge",
            receiver="advocate",
            payload={"status": "synthesis_complete"},
            correlation_id="request-123",
        )

        assert message.message_type == "response"
        assert message.sender == "judge"
        assert message.receiver == "advocate"
        assert message.correlation_id == "request-123"
        assert len(message.message_id) > 0
        assert message.timestamp > 0

    def test_create_event(self) -> None:
        """Test create_event factory method."""
        message = MessageEnvelope.create_event(
            sender="adversary",
            receiver="judge",
            payload={"event": "analysis_complete", "case_id": "case-001"},
        )

        assert message.message_type == "event"
        assert message.sender == "adversary"
        assert message.receiver == "judge"
        assert message.correlation_id is None
        assert len(message.message_id) > 0
        assert message.timestamp > 0

    def test_factory_generates_unique_ids(self) -> None:
        """Test that factory methods generate unique message IDs."""
        message1 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={},
        )
        message2 = MessageEnvelope.create_request(
            sender="advocate",
            receiver="judge",
            payload={},
        )

        assert message1.message_id != message2.message_id
