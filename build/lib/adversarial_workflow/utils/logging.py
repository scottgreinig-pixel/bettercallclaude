"""
Structured logging and telemetry system for adversarial workflow.

This module provides comprehensive logging, metrics collection, and telemetry
for the multi-agent communication system, enabling monitoring, debugging,
and performance analysis.

Features:
- Structured JSON logging with contextual information
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Performance metrics and timing instrumentation
- Agent-specific logging contexts
- Message flow tracing
- Error tracking and aggregation
- Export to multiple formats (JSON, CSV, console)
"""

import json
import logging
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class LogLevel(Enum):
    """Log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Types of metrics collected."""

    COUNTER = "counter"  # Incrementing count
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurement


@dataclass
class LogEntry:
    """
    Structured log entry with contextual information.

    Attributes:
        timestamp: ISO 8601 timestamp
        level: Log severity level
        message: Log message content
        logger_name: Name of logger that created entry
        agent_id: Optional agent identifier
        correlation_id: Optional correlation ID for message tracing
        metadata: Additional contextual data
    """

    timestamp: str
    level: str
    message: str
    logger_name: str
    agent_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert log entry to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Metric:
    """
    Performance metric with timestamp and metadata.

    Attributes:
        name: Metric name
        type: Metric type (counter, gauge, histogram, timer)
        value: Metric value
        timestamp: ISO 8601 timestamp
        tags: Optional tags for filtering/grouping
    """

    name: str
    type: MetricType
    value: float
    timestamp: str
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert metric to dictionary."""
        data = asdict(self)
        data["type"] = self.type.value
        return data


class StructuredLogger:
    """
    Structured logger with contextual information and JSON output.

    Provides logging with rich contextual data, agent identification,
    correlation IDs for message tracing, and structured output formats.
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        output_file: Path | None = None,
        console_output: bool = True,
    ) -> None:
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically module or component name)
            level: Minimum log level to record
            output_file: Optional file path for JSON log output
            console_output: Whether to also output to console
        """
        self.name = name
        self.level = level
        self.output_file = output_file
        self.console_output = console_output
        self.log_entries: list[LogEntry] = []

        # Set up Python logging
        self._setup_python_logger()

    def _setup_python_logger(self) -> None:
        """Configure Python logging infrastructure."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.level.value))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(console_handler)

        # File handler for JSON logs
        if self.output_file:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def _create_entry(
        self,
        level: LogLevel,
        message: str,
        agent_id: str | None = None,
        correlation_id: str | None = None,
        **metadata: Any,
    ) -> LogEntry:
        """Create a structured log entry."""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level.value,
            message=message,
            logger_name=self.name,
            agent_id=agent_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        self.log_entries.append(entry)

        # Write to file if configured
        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(entry.to_json() + "\n")

        return entry

    def debug(
        self,
        message: str,
        agent_id: str | None = None,
        correlation_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log debug message."""
        if self._should_log(LogLevel.DEBUG):
            self._create_entry(LogLevel.DEBUG, message, agent_id, correlation_id, **metadata)
            self.logger.debug(message, extra=metadata)

    def info(
        self,
        message: str,
        agent_id: str | None = None,
        correlation_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log info message."""
        if self._should_log(LogLevel.INFO):
            self._create_entry(LogLevel.INFO, message, agent_id, correlation_id, **metadata)
            self.logger.info(message, extra=metadata)

    def warning(
        self,
        message: str,
        agent_id: str | None = None,
        correlation_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log warning message."""
        if self._should_log(LogLevel.WARNING):
            self._create_entry(LogLevel.WARNING, message, agent_id, correlation_id, **metadata)
            self.logger.warning(message, extra=metadata)

    def error(
        self,
        message: str,
        agent_id: str | None = None,
        correlation_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log error message."""
        if self._should_log(LogLevel.ERROR):
            self._create_entry(LogLevel.ERROR, message, agent_id, correlation_id, **metadata)
            self.logger.error(message, extra=metadata)

    def critical(
        self,
        message: str,
        agent_id: str | None = None,
        correlation_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log critical message."""
        if self._should_log(LogLevel.CRITICAL):
            self._create_entry(LogLevel.CRITICAL, message, agent_id, correlation_id, **metadata)
            self.logger.critical(message, extra=metadata)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if log level should be recorded."""
        level_priority = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_priority[level] >= level_priority[self.level]

    def get_entries(
        self,
        level: LogLevel | None = None,
        agent_id: str | None = None,
        correlation_id: str | None = None,
    ) -> list[LogEntry]:
        """
        Retrieve log entries with optional filtering.

        Args:
            level: Filter by log level
            agent_id: Filter by agent ID
            correlation_id: Filter by correlation ID

        Returns:
            List of matching log entries
        """
        entries = self.log_entries

        if level:
            entries = [e for e in entries if e.level == level.value]
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        if correlation_id:
            entries = [e for e in entries if e.correlation_id == correlation_id]

        return entries

    def clear(self) -> None:
        """Clear all stored log entries."""
        self.log_entries.clear()


class MetricsCollector:
    """
    Metrics collection and aggregation system.

    Collects performance metrics, timing data, and system statistics
    for monitoring and analysis.
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.metrics: list[Metric] = []
        self.counters: dict[str, float] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}

    def increment_counter(self, name: str, value: float = 1.0, **tags: str) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Value to add (default 1.0)
            tags: Optional tags for filtering
        """
        key = self._make_key(name, tags)
        self.counters[key] = self.counters.get(key, 0.0) + value
        self._record_metric(name, MetricType.COUNTER, self.counters[key], tags)

    def set_gauge(self, name: str, value: float, **tags: str) -> None:
        """
        Set a gauge metric to specific value.

        Args:
            name: Gauge name
            value: Current value
            tags: Optional tags for filtering
        """
        key = self._make_key(name, tags)
        self.gauges[key] = value
        self._record_metric(name, MetricType.GAUGE, value, tags)

    def record_histogram(self, name: str, value: float, **tags: str) -> None:
        """
        Record a value in a histogram.

        Args:
            name: Histogram name
            value: Value to record
            tags: Optional tags for filtering
        """
        key = self._make_key(name, tags)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        self._record_metric(name, MetricType.HISTOGRAM, value, tags)

    def record_timer(self, name: str, duration: float, **tags: str) -> None:
        """
        Record a timing measurement.

        Args:
            name: Timer name
            duration: Duration in seconds
            tags: Optional tags for filtering
        """
        self._record_metric(name, MetricType.TIMER, duration, tags)

    @contextmanager
    def timer(self, name: str, **tags: str) -> Generator[None, None, None]:
        """
        Context manager for timing code blocks.

        Usage:
            with metrics.timer("operation_name"):
                # code to time
                pass
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timer(name, duration, **tags)

    def _make_key(self, name: str, tags: dict[str, str]) -> str:
        """Create unique key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def _record_metric(
        self, name: str, metric_type: MetricType, value: float, tags: dict[str, str]
    ) -> None:
        """Record a metric with timestamp."""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=datetime.utcnow().isoformat(),
            tags=tags,
        )
        self.metrics.append(metric)

    def get_metrics(
        self, name: str | None = None, metric_type: MetricType | None = None
    ) -> list[Metric]:
        """
        Retrieve metrics with optional filtering.

        Args:
            name: Filter by metric name
            metric_type: Filter by metric type

        Returns:
            List of matching metrics
        """
        metrics = self.metrics

        if name:
            metrics = [m for m in metrics if m.name == name]
        if metric_type:
            metrics = [m for m in metrics if m.type == metric_type]

        return metrics

    def get_histogram_stats(self, name: str, **tags: str) -> dict[str, float] | None:
        """
        Get statistical summary of histogram.

        Args:
            name: Histogram name
            tags: Optional tags for filtering

        Returns:
            Dictionary with min, max, mean, median, p95, p99
        """
        key = self._make_key(name, tags)
        values = self.histograms.get(key)

        if not values:
            return None

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / count,
            "median": sorted_values[count // 2],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
            "count": count,
        }

    def clear(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()


class TelemetrySystem:
    """
    Comprehensive telemetry system combining logging and metrics.

    Provides unified interface for structured logging, metrics collection,
    and performance monitoring.
    """

    def __init__(
        self,
        logger_name: str = "adversarial_workflow",
        log_level: LogLevel = LogLevel.INFO,
        log_file: Path | None = None,
    ) -> None:
        """
        Initialize telemetry system.

        Args:
            logger_name: Name for structured logger
            log_level: Minimum log level to record
            log_file: Optional file path for JSON logs
        """
        self.logger = StructuredLogger(logger_name, log_level, log_file)
        self.metrics = MetricsCollector()

    def log_message_sent(
        self, message_type: str, sender: str, recipient: str, correlation_id: str
    ) -> None:
        """Log message sent event."""
        self.logger.info(
            f"Message sent: {message_type}",
            agent_id=sender,
            correlation_id=correlation_id,
            recipient=recipient,
            message_type=message_type,
        )
        self.metrics.increment_counter("messages_sent", agent=sender, type=message_type)

    def log_message_received(
        self, message_type: str, sender: str, recipient: str, correlation_id: str
    ) -> None:
        """Log message received event."""
        self.logger.info(
            f"Message received: {message_type}",
            agent_id=recipient,
            correlation_id=correlation_id,
            sender=sender,
            message_type=message_type,
        )
        self.metrics.increment_counter("messages_received", agent=recipient, type=message_type)

    def log_agent_created(self, agent_id: str, agent_type: str) -> None:
        """Log agent creation event."""
        self.logger.info(f"Agent created: {agent_id}", agent_id=agent_id, agent_type=agent_type)
        self.metrics.increment_counter("agents_created", type=agent_type)

    def log_error(self, message: str, error: Exception, agent_id: str | None = None) -> None:
        """Log error with exception details."""
        self.logger.error(
            message,
            agent_id=agent_id,
            error_type=type(error).__name__,
            error_message=str(error),
        )
        self.metrics.increment_counter("errors", error_type=type(error).__name__)

    @contextmanager
    def trace_operation(
        self, operation_name: str, agent_id: str | None = None
    ) -> Generator[None, None, None]:
        """
        Trace operation execution time and log start/end.

        Usage:
            with telemetry.trace_operation("analyze_case"):
                # operation code
                pass
        """
        start_time = time.time()
        self.logger.debug(f"Starting operation: {operation_name}", agent_id=agent_id)

        try:
            yield
        except Exception as e:
            self.log_error(f"Operation failed: {operation_name}", e, agent_id)
            raise
        finally:
            duration = time.time() - start_time
            self.logger.debug(
                f"Completed operation: {operation_name}",
                agent_id=agent_id,
                duration_seconds=duration,
            )
            self.metrics.record_timer(operation_name, duration, agent=agent_id or "system")

    def get_summary(self) -> dict[str, Any]:
        """
        Get telemetry summary.

        Returns:
            Dictionary with log and metric summaries
        """
        return {
            "logs": {
                "total": len(self.logger.log_entries),
                "by_level": {
                    level.value: len(self.logger.get_entries(level=level)) for level in LogLevel
                },
            },
            "metrics": {
                "total": len(self.metrics.metrics),
                "counters": len(self.metrics.counters),
                "gauges": len(self.metrics.gauges),
                "histograms": len(self.metrics.histograms),
            },
        }
