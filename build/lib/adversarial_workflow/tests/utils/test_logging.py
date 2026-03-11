"""
Tests for structured logging and telemetry system.

This module contains comprehensive tests for the structured logging, metrics collection,
and telemetry system that handles agent-based communication monitoring.

Test Coverage:
- LogEntry and Metric dataclass functionality
- StructuredLogger logging methods and filtering
- MetricsCollector metric recording and statistical analysis
- TelemetrySystem integration and domain-specific methods
- Context managers (timer, trace_operation)
- Exception handling and edge cases
"""

import json
import time
from pathlib import Path

import pytest

from adversarial_workflow.utils.logging import (
    LogEntry,
    LogLevel,
    Metric,
    MetricsCollector,
    MetricType,
    StructuredLogger,
    TelemetrySystem,
)


class TestLogEntry:
    """Test cases for LogEntry dataclass."""

    def test_create_log_entry(self) -> None:
        """Test creating a basic log entry."""
        entry = LogEntry(
            timestamp="2024-01-05T10:00:00",
            level="INFO",
            message="Test message",
            logger_name="test_logger",
        )

        assert entry.timestamp == "2024-01-05T10:00:00"
        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.logger_name == "test_logger"
        assert entry.agent_id is None
        assert entry.correlation_id is None
        assert entry.metadata == {}

    def test_log_entry_with_agent_context(self) -> None:
        """Test log entry with agent ID and correlation ID."""
        entry = LogEntry(
            timestamp="2024-01-05T10:00:00",
            level="INFO",
            message="Agent message",
            logger_name="test_logger",
            agent_id="agent_001",
            correlation_id="corr_123",
        )

        assert entry.agent_id == "agent_001"
        assert entry.correlation_id == "corr_123"

    def test_log_entry_with_metadata(self) -> None:
        """Test log entry with additional metadata."""
        metadata = {"user": "john", "action": "login", "ip": "192.168.1.1"}
        entry = LogEntry(
            timestamp="2024-01-05T10:00:00",
            level="INFO",
            message="User login",
            logger_name="auth_logger",
            metadata=metadata,
        )

        assert entry.metadata == metadata
        assert entry.metadata["user"] == "john"

    def test_log_entry_to_dict(self) -> None:
        """Test converting LogEntry to dictionary."""
        entry = LogEntry(
            timestamp="2024-01-05T10:00:00",
            level="INFO",
            message="Test",
            logger_name="test",
            agent_id="agent_001",
            metadata={"key": "value"},
        )

        result = entry.to_dict()
        assert isinstance(result, dict)
        assert result["timestamp"] == "2024-01-05T10:00:00"
        assert result["level"] == "INFO"
        assert result["message"] == "Test"
        assert result["agent_id"] == "agent_001"
        assert result["metadata"]["key"] == "value"

    def test_log_entry_to_json(self) -> None:
        """Test converting LogEntry to JSON string."""
        entry = LogEntry(
            timestamp="2024-01-05T10:00:00",
            level="INFO",
            message="Test",
            logger_name="test",
        )

        json_str = entry.to_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test"

    def test_log_entry_string_representation(self) -> None:
        """Test LogEntry default string representation."""
        entry = LogEntry(
            timestamp="2024-01-05T10:00:00",
            level="INFO",
            message="Test message",
            logger_name="test",
        )

        # Dataclass __str__ should work
        str_repr = str(entry)
        assert "LogEntry" in str_repr or "Test message" in str_repr


class TestMetric:
    """Test cases for Metric dataclass."""

    def test_create_metric(self) -> None:
        """Test creating a basic metric."""
        metric = Metric(
            name="request_count",
            type=MetricType.COUNTER,
            value=42.0,
            timestamp="2024-01-05T10:00:00",
        )

        assert metric.name == "request_count"
        assert metric.type == MetricType.COUNTER
        assert metric.value == 42.0
        assert metric.timestamp == "2024-01-05T10:00:00"
        assert metric.tags == {}

    def test_metric_with_tags(self) -> None:
        """Test metric with tags."""
        tags = {"service": "api", "endpoint": "/users"}
        metric = Metric(
            name="request_latency",
            type=MetricType.TIMER,
            value=0.25,
            timestamp="2024-01-05T10:00:00",
            tags=tags,
        )

        assert metric.tags == tags
        assert metric.tags["service"] == "api"

    def test_metric_to_dict(self) -> None:
        """Test converting Metric to dictionary."""
        metric = Metric(
            name="memory_usage",
            type=MetricType.GAUGE,
            value=1024.0,
            timestamp="2024-01-05T10:00:00",
            tags={"host": "server1"},
        )

        result = metric.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == "memory_usage"
        assert result["type"] == "gauge"  # Enum value converted
        assert result["value"] == 1024.0
        assert result["tags"]["host"] == "server1"


class TestStructuredLogger:
    """Test cases for StructuredLogger."""

    def test_logger_initialization(self) -> None:
        """Test logger initialization with default parameters."""
        logger = StructuredLogger("test_logger")

        assert logger.name == "test_logger"
        assert logger.level == LogLevel.INFO
        assert logger.output_file is None
        assert logger.console_output is True
        assert len(logger.log_entries) == 0

    def test_logger_with_custom_level(self) -> None:
        """Test logger with custom log level."""
        logger = StructuredLogger("test_logger", level=LogLevel.WARNING)

        assert logger.level == LogLevel.WARNING

    def test_log_debug_message(self) -> None:
        """Test logging debug message."""
        logger = StructuredLogger("test_logger", level=LogLevel.DEBUG, console_output=False)

        logger.debug("Debug message", agent_id="agent_001", test_key="test_value")

        assert len(logger.log_entries) == 1
        entry = logger.log_entries[0]
        assert entry.level == "DEBUG"
        assert entry.message == "Debug message"
        assert entry.agent_id == "agent_001"
        assert entry.metadata["test_key"] == "test_value"

    def test_log_info_message(self) -> None:
        """Test logging info message."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Info message", correlation_id="corr_123")

        assert len(logger.log_entries) == 1
        entry = logger.log_entries[0]
        assert entry.level == "INFO"
        assert entry.message == "Info message"
        assert entry.correlation_id == "corr_123"

    def test_log_warning_message(self) -> None:
        """Test logging warning message."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.warning("Warning message")

        assert len(logger.log_entries) == 1
        assert logger.log_entries[0].level == "WARNING"

    def test_log_error_message(self) -> None:
        """Test logging error message."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.error("Error message")

        assert len(logger.log_entries) == 1
        assert logger.log_entries[0].level == "ERROR"

    def test_log_critical_message(self) -> None:
        """Test logging critical message."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.critical("Critical message")

        assert len(logger.log_entries) == 1
        assert logger.log_entries[0].level == "CRITICAL"

    def test_log_level_filtering(self) -> None:
        """Test that log level filtering works correctly."""
        logger = StructuredLogger("test_logger", level=LogLevel.WARNING, console_output=False)

        logger.debug("Debug message")  # Should not be logged
        logger.info("Info message")  # Should not be logged
        logger.warning("Warning message")  # Should be logged
        logger.error("Error message")  # Should be logged

        assert len(logger.log_entries) == 2
        assert logger.log_entries[0].level == "WARNING"
        assert logger.log_entries[1].level == "ERROR"

    def test_get_entries_no_filter(self) -> None:
        """Test retrieving all log entries without filters."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Message 1")
        logger.warning("Message 2")
        logger.error("Message 3")

        entries = logger.get_entries()
        assert len(entries) == 3

    def test_get_entries_by_level(self) -> None:
        """Test filtering entries by log level."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Info 1")
        logger.warning("Warning 1")
        logger.info("Info 2")
        logger.error("Error 1")

        info_entries = logger.get_entries(level=LogLevel.INFO)
        assert len(info_entries) == 2
        assert all(e.level == "INFO" for e in info_entries)

    def test_get_entries_by_agent_id(self) -> None:
        """Test filtering entries by agent ID."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Agent 1 message", agent_id="agent_001")
        logger.info("Agent 2 message", agent_id="agent_002")
        logger.info("Agent 1 again", agent_id="agent_001")

        agent_entries = logger.get_entries(agent_id="agent_001")
        assert len(agent_entries) == 2
        assert all(e.agent_id == "agent_001" for e in agent_entries)

    def test_get_entries_by_correlation_id(self) -> None:
        """Test filtering entries by correlation ID."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Message 1", correlation_id="corr_123")
        logger.info("Message 2", correlation_id="corr_456")
        logger.info("Message 3", correlation_id="corr_123")

        corr_entries = logger.get_entries(correlation_id="corr_123")
        assert len(corr_entries) == 2
        assert all(e.correlation_id == "corr_123" for e in corr_entries)

    def test_get_entries_multiple_filters(self) -> None:
        """Test filtering with multiple criteria."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Info from agent 1", agent_id="agent_001", correlation_id="corr_123")
        logger.warning("Warning from agent 1", agent_id="agent_001", correlation_id="corr_123")
        logger.info("Info from agent 2", agent_id="agent_002", correlation_id="corr_123")

        filtered = logger.get_entries(
            level=LogLevel.INFO, agent_id="agent_001", correlation_id="corr_123"
        )
        assert len(filtered) == 1
        assert filtered[0].level == "INFO"
        assert filtered[0].agent_id == "agent_001"

    def test_clear_log_entries(self) -> None:
        """Test clearing all log entries."""
        logger = StructuredLogger("test_logger", console_output=False)

        logger.info("Message 1")
        logger.info("Message 2")
        assert len(logger.log_entries) == 2

        logger.clear()
        assert len(logger.log_entries) == 0

    def test_file_output(self, tmp_path: Path) -> None:
        """Test logging to file."""
        log_file = tmp_path / "test.log"
        logger = StructuredLogger("test_logger", output_file=log_file, console_output=False)

        logger.info("File message")

        # Verify file was created and contains JSON
        assert log_file.exists()
        content = log_file.read_text()
        assert "File message" in content
        assert "INFO" in content

        # Verify it's valid JSON
        json.loads(content)


class TestMetricsCollector:
    """Test cases for MetricsCollector."""

    def test_collector_initialization(self) -> None:
        """Test metrics collector initialization."""
        collector = MetricsCollector()

        assert len(collector.metrics) == 0
        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
        assert len(collector.histograms) == 0

    def test_increment_counter(self) -> None:
        """Test incrementing a counter."""
        collector = MetricsCollector()

        collector.increment_counter("requests")
        assert collector.counters["requests"] == 1.0

        collector.increment_counter("requests")
        assert collector.counters["requests"] == 2.0

    def test_increment_counter_custom_value(self) -> None:
        """Test incrementing counter with custom value."""
        collector = MetricsCollector()

        collector.increment_counter("bytes_sent", value=1024.0)
        assert collector.counters["bytes_sent"] == 1024.0

        collector.increment_counter("bytes_sent", value=512.0)
        assert collector.counters["bytes_sent"] == 1536.0

    def test_increment_counter_with_tags(self) -> None:
        """Test counter with tags."""
        collector = MetricsCollector()

        collector.increment_counter("requests", service="api", endpoint="/users")
        collector.increment_counter("requests", service="api", endpoint="/posts")

        # Different tag combinations create different keys
        assert len(collector.counters) == 2

    def test_set_gauge(self) -> None:
        """Test setting a gauge value."""
        collector = MetricsCollector()

        collector.set_gauge("memory_usage", 512.0)
        assert collector.gauges["memory_usage"] == 512.0

        collector.set_gauge("memory_usage", 768.0)
        assert collector.gauges["memory_usage"] == 768.0  # Overwritten

    def test_set_gauge_with_tags(self) -> None:
        """Test gauge with tags."""
        collector = MetricsCollector()

        collector.set_gauge("cpu_usage", 45.0, host="server1")
        collector.set_gauge("cpu_usage", 78.0, host="server2")

        assert len(collector.gauges) == 2

    def test_record_histogram(self) -> None:
        """Test recording histogram values."""
        collector = MetricsCollector()

        collector.record_histogram("response_time", 0.15)
        collector.record_histogram("response_time", 0.23)
        collector.record_histogram("response_time", 0.18)

        assert len(collector.histograms["response_time"]) == 3
        assert 0.15 in collector.histograms["response_time"]

    def test_record_timer(self) -> None:
        """Test recording timer measurement."""
        collector = MetricsCollector()

        collector.record_timer("operation_duration", 1.25)

        # Timer creates a metric
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]
        assert metric.type == MetricType.TIMER
        assert metric.value == 1.25

    def test_timer_context_manager(self) -> None:
        """Test timer context manager."""
        collector = MetricsCollector()

        with collector.timer("test_operation"):
            time.sleep(0.01)  # Small sleep to ensure measurable time

        # Should have recorded a timer metric
        metrics = collector.get_metrics(name="test_operation", metric_type=MetricType.TIMER)
        assert len(metrics) == 1
        assert metrics[0].value > 0  # Duration should be positive

    def test_get_metrics_no_filter(self) -> None:
        """Test retrieving all metrics without filters."""
        collector = MetricsCollector()

        collector.increment_counter("counter1")
        collector.set_gauge("gauge1", 100.0)
        collector.record_timer("timer1", 0.5)

        all_metrics = collector.get_metrics()
        assert len(all_metrics) == 3

    def test_get_metrics_by_name(self) -> None:
        """Test filtering metrics by name."""
        collector = MetricsCollector()

        collector.increment_counter("requests")
        collector.increment_counter("requests")
        collector.set_gauge("memory", 512.0)

        request_metrics = collector.get_metrics(name="requests")
        assert len(request_metrics) == 2

    def test_get_metrics_by_type(self) -> None:
        """Test filtering metrics by type."""
        collector = MetricsCollector()

        collector.increment_counter("counter1")
        collector.increment_counter("counter2")
        collector.set_gauge("gauge1", 100.0)

        counter_metrics = collector.get_metrics(metric_type=MetricType.COUNTER)
        assert len(counter_metrics) == 2
        assert all(m.type == MetricType.COUNTER for m in counter_metrics)

    def test_histogram_stats_basic(self) -> None:
        """Test basic histogram statistics."""
        collector = MetricsCollector()

        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for val in values:
            collector.record_histogram("test_metric", val)

        stats = collector.get_histogram_stats("test_metric")
        assert stats is not None
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["count"] == 5

    def test_histogram_stats_percentiles(self) -> None:
        """Test histogram percentile calculations."""
        collector = MetricsCollector()

        # Add 100 values
        for i in range(100):
            collector.record_histogram("latency", float(i))

        stats = collector.get_histogram_stats("latency")
        assert stats is not None
        assert stats["p95"] == 95.0
        assert stats["p99"] == 99.0

    def test_histogram_stats_nonexistent(self) -> None:
        """Test histogram stats for nonexistent metric."""
        collector = MetricsCollector()

        stats = collector.get_histogram_stats("nonexistent")
        assert stats is None

    def test_histogram_stats_with_tags(self) -> None:
        """Test histogram stats with tags."""
        collector = MetricsCollector()

        collector.record_histogram("latency", 1.0, service="api")
        collector.record_histogram("latency", 2.0, service="api")
        collector.record_histogram("latency", 10.0, service="db")

        api_stats = collector.get_histogram_stats("latency", service="api")
        assert api_stats is not None
        assert api_stats["count"] == 2

    def test_clear_metrics(self) -> None:
        """Test clearing all metrics."""
        collector = MetricsCollector()

        collector.increment_counter("counter")
        collector.set_gauge("gauge", 100.0)
        collector.record_histogram("histogram", 1.0)

        collector.clear()

        assert len(collector.metrics) == 0
        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
        assert len(collector.histograms) == 0


class TestTelemetrySystem:
    """Test cases for TelemetrySystem integration."""

    def test_telemetry_initialization(self) -> None:
        """Test telemetry system initialization."""
        telemetry = TelemetrySystem()

        assert telemetry.logger.name == "adversarial_workflow"
        assert telemetry.logger.level == LogLevel.INFO
        assert isinstance(telemetry.metrics, MetricsCollector)

    def test_telemetry_custom_logger_name(self) -> None:
        """Test telemetry with custom logger name."""
        telemetry = TelemetrySystem(logger_name="custom_logger")

        assert telemetry.logger.name == "custom_logger"

    def test_log_message_sent(self) -> None:
        """Test logging message sent event."""
        telemetry = TelemetrySystem()
        telemetry.logger.console_output = False

        telemetry.log_message_sent(
            message_type="REQUEST",
            sender="agent_001",
            recipient="agent_002",
            correlation_id="corr_123",
        )

        # Check log entry
        entries = telemetry.logger.get_entries()
        assert len(entries) == 1
        assert "Message sent: REQUEST" in entries[0].message
        assert entries[0].agent_id == "agent_001"

        # Check metric
        metrics = telemetry.metrics.get_metrics(name="messages_sent")
        assert len(metrics) == 1

    def test_log_message_received(self) -> None:
        """Test logging message received event."""
        telemetry = TelemetrySystem()
        telemetry.logger.console_output = False

        telemetry.log_message_received(
            message_type="RESPONSE",
            sender="agent_001",
            recipient="agent_002",
            correlation_id="corr_123",
        )

        entries = telemetry.logger.get_entries()
        assert len(entries) == 1
        assert "Message received: RESPONSE" in entries[0].message

        metrics = telemetry.metrics.get_metrics(name="messages_received")
        assert len(metrics) == 1

    def test_log_agent_created(self) -> None:
        """Test logging agent creation event."""
        telemetry = TelemetrySystem()
        telemetry.logger.console_output = False

        telemetry.log_agent_created(agent_id="agent_001", agent_type="researcher")

        entries = telemetry.logger.get_entries()
        assert len(entries) == 1
        assert "Agent created: agent_001" in entries[0].message

        metrics = telemetry.metrics.get_metrics(name="agents_created")
        assert len(metrics) == 1

    def test_log_error(self) -> None:
        """Test logging error with exception."""
        telemetry = TelemetrySystem()
        telemetry.logger.console_output = False

        error = ValueError("Test error")
        telemetry.log_error("Operation failed", error, agent_id="agent_001")

        entries = telemetry.logger.get_entries(level=LogLevel.ERROR)
        assert len(entries) == 1
        assert "Operation failed" in entries[0].message
        assert entries[0].metadata["error_type"] == "ValueError"

        metrics = telemetry.metrics.get_metrics(name="errors")
        assert len(metrics) == 1

    def test_trace_operation_success(self) -> None:
        """Test tracing successful operation."""
        telemetry = TelemetrySystem(log_level=LogLevel.DEBUG)
        telemetry.logger.console_output = False

        with telemetry.trace_operation("test_operation", agent_id="agent_001"):
            time.sleep(0.01)

        # Should have debug logs for start and completion
        entries = telemetry.logger.get_entries(level=LogLevel.DEBUG)
        assert len(entries) >= 2  # Start and completion

        # Should have timer metric
        timer_metrics = telemetry.metrics.get_metrics(
            name="test_operation", metric_type=MetricType.TIMER
        )
        assert len(timer_metrics) == 1
        assert timer_metrics[0].value > 0

    def test_trace_operation_with_exception(self) -> None:
        """Test tracing operation that raises exception."""
        telemetry = TelemetrySystem(log_level=LogLevel.DEBUG)
        telemetry.logger.console_output = False

        with pytest.raises(ValueError):
            with telemetry.trace_operation("failing_operation"):
                raise ValueError("Operation failed")

        # Should have error log
        error_entries = telemetry.logger.get_entries(level=LogLevel.ERROR)
        assert len(error_entries) == 1
        assert "Operation failed: failing_operation" in error_entries[0].message

        # Should still have timer metric (finally block)
        timer_metrics = telemetry.metrics.get_metrics(
            name="failing_operation", metric_type=MetricType.TIMER
        )
        assert len(timer_metrics) == 1

    def test_get_summary(self) -> None:
        """Test getting telemetry summary."""
        telemetry = TelemetrySystem()
        telemetry.logger.console_output = False

        telemetry.logger.info("Info message")
        telemetry.logger.warning("Warning message")
        telemetry.logger.error("Error message")
        telemetry.metrics.increment_counter("test_counter")
        telemetry.metrics.set_gauge("test_gauge", 100.0)

        summary = telemetry.get_summary()

        assert summary["logs"]["total"] == 3
        assert summary["logs"]["by_level"]["INFO"] == 1
        assert summary["logs"]["by_level"]["WARNING"] == 1
        assert summary["logs"]["by_level"]["ERROR"] == 1
        assert summary["metrics"]["total"] == 2
        assert summary["metrics"]["counters"] == 1
        assert summary["metrics"]["gauges"] == 1


class TestEdgeCases:
    """Test cases for edge cases and error handling."""

    def test_empty_logger_name(self) -> None:
        """Test logger with empty name."""
        logger = StructuredLogger("", console_output=False)
        logger.info("Test")

        assert logger.name == ""
        assert len(logger.log_entries) == 1

    def test_log_with_none_metadata(self) -> None:
        """Test logging with None values in metadata."""
        logger = StructuredLogger("test", console_output=False)
        logger.info("Test", none_value=None, valid_value="test")

        entry = logger.log_entries[0]
        assert entry.metadata["none_value"] is None
        assert entry.metadata["valid_value"] == "test"

    def test_histogram_single_value(self) -> None:
        """Test histogram statistics with single value."""
        collector = MetricsCollector()
        collector.record_histogram("test", 42.0)

        stats = collector.get_histogram_stats("test")
        assert stats is not None
        assert stats["min"] == 42.0
        assert stats["max"] == 42.0
        assert stats["mean"] == 42.0
        assert stats["median"] == 42.0

    def test_metrics_with_special_characters_in_tags(self) -> None:
        """Test metrics with special characters in tag values."""
        collector = MetricsCollector()

        collector.increment_counter("requests", path="/api/users?sort=name&order=asc")

        assert len(collector.counters) == 1

    def test_timer_with_zero_duration(self) -> None:
        """Test timer that completes instantly."""
        collector = MetricsCollector()

        with collector.timer("instant_op"):
            pass  # No delay

        metrics = collector.get_metrics(name="instant_op")
        assert len(metrics) == 1
        assert metrics[0].value >= 0  # Could be zero or very small

    def test_multiple_file_outputs(self, tmp_path: Path) -> None:
        """Test that multiple loggers can write to different files."""
        file1 = tmp_path / "log1.log"
        file2 = tmp_path / "log2.log"

        logger1 = StructuredLogger("logger1", output_file=file1, console_output=False)
        logger2 = StructuredLogger("logger2", output_file=file2, console_output=False)

        logger1.info("Logger 1 message")
        logger2.info("Logger 2 message")

        assert file1.exists()
        assert file2.exists()
        assert "Logger 1 message" in file1.read_text()
        assert "Logger 2 message" in file2.read_text()
