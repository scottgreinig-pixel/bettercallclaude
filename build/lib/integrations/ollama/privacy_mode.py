"""
Privacy mode for sensitive legal document processing.

Routes requests to local Ollama when privacy is required,
with automatic fallback to cloud when local is unavailable.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.integrations.ollama.client import (
    ChatMessage,
    OllamaClient,
    OllamaModel,
    OllamaResponse,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)


class PrivacyLevel(Enum):
    """Document privacy classification for routing decisions."""

    PUBLIC = "public"
    """Can use cloud services - no sensitive data."""

    CONFIDENTIAL = "confidential"
    """Prefer local processing - business sensitive data."""

    PRIVILEGED = "privileged"
    """Local only, no fallback - attorney-client privilege."""

    @property
    def allows_cloud(self) -> bool:
        """Check if cloud processing is allowed."""
        return self in (PrivacyLevel.PUBLIC, PrivacyLevel.CONFIDENTIAL)

    @property
    def requires_local(self) -> bool:
        """Check if local processing is required."""
        return self == PrivacyLevel.PRIVILEGED

    @property
    def description(self) -> dict[str, str]:
        """Return multilingual description."""
        descriptions = {
            PrivacyLevel.PUBLIC: {
                "de": "Öffentlich - Cloud-Verarbeitung erlaubt",
                "fr": "Public - Traitement cloud autorisé",
                "it": "Pubblico - Elaborazione cloud consentita",
                "en": "Public - Cloud processing allowed",
            },
            PrivacyLevel.CONFIDENTIAL: {
                "de": "Vertraulich - Lokale Verarbeitung bevorzugt",
                "fr": "Confidentiel - Traitement local préféré",
                "it": "Riservato - Elaborazione locale preferita",
                "en": "Confidential - Local processing preferred",
            },
            PrivacyLevel.PRIVILEGED: {
                "de": "Privilegiert - Nur lokale Verarbeitung",
                "fr": "Privilégié - Traitement local uniquement",
                "it": "Privilegiato - Solo elaborazione locale",
                "en": "Privileged - Local processing only",
            },
        }
        return descriptions.get(self, descriptions[PrivacyLevel.CONFIDENTIAL])


@dataclass
class PrivacyConfig:
    """Privacy mode configuration."""

    default_level: PrivacyLevel = PrivacyLevel.CONFIDENTIAL
    allow_cloud_fallback: bool = True
    local_only_patterns: list[str] = field(default_factory=list)
    log_routing_decisions: bool = True
    warn_on_cloud_usage: bool = True
    auto_detect_sensitivity: bool = True

    def __post_init__(self) -> None:
        """Set default local-only patterns for Swiss legal context."""
        if not self.local_only_patterns:
            self.local_only_patterns = [
                # German patterns
                r"(?i)anwalt.*geheimnis",  # Attorney-client privilege
                r"(?i)mandatsgeheimnis",  # Client confidentiality
                r"(?i)berufsgeheimnis",  # Professional secrecy
                r"(?i)geschäftsgeheimnis",  # Trade secret
                r"(?i)vertraulich",  # Confidential
                r"(?i)streng\s+vertraulich",  # Strictly confidential
                # French patterns
                r"(?i)secret\s+professionnel",  # Professional secrecy
                r"(?i)confidentiel",  # Confidential
                r"(?i)strictement\s+confidentiel",  # Strictly confidential
                # Italian patterns
                r"(?i)segreto\s+professionale",  # Professional secrecy
                r"(?i)riservato",  # Confidential
                r"(?i)strettamente\s+riservato",  # Strictly confidential
                # Legal references
                r"(?i)Art\.\s*321\s*StGB",  # Swiss Penal Code - professional secrecy
                r"(?i)Art\.\s*13\s*BGFA",  # Lawyers Act - professional secrecy
            ]


@dataclass
class RoutingDecision:
    """Record of a routing decision for audit purposes."""

    timestamp: datetime
    privacy_level: PrivacyLevel
    backend_used: str  # "local" or "cloud"
    fallback_used: bool
    reason: str
    prompt_hash: str | None = None  # Hash of prompt for audit trail

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "privacy_level": self.privacy_level.value,
            "backend_used": self.backend_used,
            "fallback_used": self.fallback_used,
            "reason": self.reason,
            "prompt_hash": self.prompt_hash,
        }


@dataclass
class PrivacyRoutingResult:
    """Result of privacy-aware request routing."""

    backend: str  # "local" or "cloud"
    response: OllamaResponse | None
    decision: RoutingDecision
    cloud_response: Any | None = None  # For cloud responses


class PrivacyViolationError(Exception):
    """Raised when privacy requirements cannot be met."""

    pass


class PrivacyRouter:
    """
    Routes AI requests based on privacy requirements.

    Decision matrix:
    - PUBLIC → Cloud preferred (faster/better)
    - CONFIDENTIAL → Local preferred, cloud fallback allowed
    - PRIVILEGED → Local only, fail if unavailable

    Swiss Legal Context:
    - Anwaltsgeheimnis (Attorney-client privilege) → PRIVILEGED
    - Geschäftsgeheimnisse (Trade secrets) → CONFIDENTIAL
    - Public court decisions → PUBLIC
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        config: PrivacyConfig | None = None,
        cloud_handler: Callable[..., Any] | None = None,
    ):
        """Initialize privacy router.

        Args:
            ollama_client: Ollama client for local processing.
            config: Privacy configuration.
            cloud_handler: Optional async function for cloud requests.
        """
        self.ollama = ollama_client
        self.config = config or PrivacyConfig()
        self.cloud_handler = cloud_handler
        self._routing_history: list[RoutingDecision] = []
        self._compiled_patterns: list[re.Pattern[str]] = [
            re.compile(p) for p in self.config.local_only_patterns
        ]

    def detect_privacy_level(self, text: str) -> PrivacyLevel:
        """Auto-detect privacy level from text content.

        Args:
            text: Text to analyze for sensitive content.

        Returns:
            Detected privacy level based on content patterns.
        """
        if not self.config.auto_detect_sensitivity:
            return self.config.default_level

        # Check for privileged content patterns
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                logger.debug(f"Detected privileged content pattern: {pattern.pattern}")
                return PrivacyLevel.PRIVILEGED

        # Check for general confidential indicators
        confidential_indicators = [
            r"(?i)intern",
            r"(?i)nicht\s+zur\s+weitergabe",
            r"(?i)privat",
            r"(?i)persönlich",
            r"(?i)à\s+usage\s+interne",
            r"(?i)uso\s+interno",
        ]

        for indicator in confidential_indicators:
            if re.search(indicator, text):
                return PrivacyLevel.CONFIDENTIAL

        return self.config.default_level

    async def route_request(
        self,
        prompt: str,
        privacy_level: PrivacyLevel | None = None,
        model: OllamaModel | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> PrivacyRoutingResult:
        """Route request to appropriate backend.

        Args:
            prompt: User prompt.
            privacy_level: Privacy level (auto-detected if not provided).
            model: Ollama model to use for local processing.
            system_prompt: Optional system prompt.
            **kwargs: Additional arguments for generation.

        Returns:
            PrivacyRoutingResult with backend used and response.

        Raises:
            PrivacyViolationError: If privacy requirements cannot be met.
        """
        # Determine privacy level
        level = privacy_level or self.detect_privacy_level(prompt)

        # Also check system prompt for sensitive patterns
        if system_prompt:
            system_level = self.detect_privacy_level(system_prompt)
            if system_level.requires_local:
                level = system_level

        logger.info(f"Routing request with privacy level: {level.value}")

        if level == PrivacyLevel.PRIVILEGED:
            return await self._route_privileged(prompt, model, system_prompt, **kwargs)
        elif level == PrivacyLevel.CONFIDENTIAL:
            return await self._route_confidential(prompt, model, system_prompt, **kwargs)
        else:  # PUBLIC
            return await self._route_public(prompt, model, system_prompt, **kwargs)

    async def _route_privileged(
        self,
        prompt: str,
        model: OllamaModel | None,
        system_prompt: str | None,
        **kwargs: Any,
    ) -> PrivacyRoutingResult:
        """Route privileged request - local only, no fallback."""
        if not await self.ollama.is_available():
            decision = self._record_decision(
                PrivacyLevel.PRIVILEGED,
                "failed",
                False,
                "Local LLM required but unavailable",
                prompt,
            )
            raise PrivacyViolationError(
                "Local LLM required for privileged content but Ollama unavailable. "
                "Please start Ollama with: `ollama serve`"
            )

        try:
            response = await self.ollama.generate(
                prompt,
                model=model,
                system_prompt=system_prompt,
                **kwargs,
            )
            decision = self._record_decision(
                PrivacyLevel.PRIVILEGED,
                "local",
                False,
                "Privileged content processed locally",
                prompt,
            )
            return PrivacyRoutingResult(
                backend="local",
                response=response,
                decision=decision,
            )
        except OllamaUnavailableError as e:
            decision = self._record_decision(
                PrivacyLevel.PRIVILEGED,
                "failed",
                False,
                f"Local processing failed: {e}",
                prompt,
            )
            raise PrivacyViolationError(
                f"Local LLM processing failed and cloud fallback not allowed: {e}"
            ) from e

    async def _route_confidential(
        self,
        prompt: str,
        model: OllamaModel | None,
        system_prompt: str | None,
        **kwargs: Any,
    ) -> PrivacyRoutingResult:
        """Route confidential request - local preferred, cloud fallback if allowed."""
        if await self.ollama.is_available():
            try:
                response = await self.ollama.generate(
                    prompt,
                    model=model,
                    system_prompt=system_prompt,
                    **kwargs,
                )
                decision = self._record_decision(
                    PrivacyLevel.CONFIDENTIAL,
                    "local",
                    False,
                    "Confidential content processed locally",
                    prompt,
                )
                return PrivacyRoutingResult(
                    backend="local",
                    response=response,
                    decision=decision,
                )
            except OllamaUnavailableError:
                logger.warning("Local processing failed, attempting cloud fallback")

        # Cloud fallback
        if self.config.allow_cloud_fallback:
            if self.config.warn_on_cloud_usage:
                logger.warning("Confidential content being sent to cloud - local LLM unavailable")

            cloud_response = await self._route_to_cloud(prompt, system_prompt, **kwargs)
            decision = self._record_decision(
                PrivacyLevel.CONFIDENTIAL,
                "cloud",
                True,
                "Fallback to cloud - local unavailable",
                prompt,
            )
            return PrivacyRoutingResult(
                backend="cloud",
                response=None,
                decision=decision,
                cloud_response=cloud_response,
            )
        else:
            decision = self._record_decision(
                PrivacyLevel.CONFIDENTIAL,
                "failed",
                False,
                "Local unavailable and cloud fallback disabled",
                prompt,
            )
            raise PrivacyViolationError(
                "Local LLM unavailable and cloud fallback is disabled for confidential content"
            )

    async def _route_public(
        self,
        prompt: str,
        model: OllamaModel | None,
        system_prompt: str | None,
        **kwargs: Any,
    ) -> PrivacyRoutingResult:
        """Route public request - cloud preferred for quality."""
        # Try cloud first for public content (better quality/speed)
        if self.cloud_handler:
            try:
                cloud_response = await self._route_to_cloud(prompt, system_prompt, **kwargs)
                decision = self._record_decision(
                    PrivacyLevel.PUBLIC,
                    "cloud",
                    False,
                    "Public content processed via cloud",
                    prompt,
                )
                return PrivacyRoutingResult(
                    backend="cloud",
                    response=None,
                    decision=decision,
                    cloud_response=cloud_response,
                )
            except Exception as e:
                logger.warning(f"Cloud processing failed: {e}, trying local")

        # Local fallback
        if await self.ollama.is_available():
            response = await self.ollama.generate(
                prompt,
                model=model,
                system_prompt=system_prompt,
                **kwargs,
            )
            decision = self._record_decision(
                PrivacyLevel.PUBLIC,
                "local",
                True if self.cloud_handler else False,
                "Public content processed locally",
                prompt,
            )
            return PrivacyRoutingResult(
                backend="local",
                response=response,
                decision=decision,
            )

        decision = self._record_decision(
            PrivacyLevel.PUBLIC,
            "failed",
            False,
            "No backend available",
            prompt,
        )
        raise PrivacyViolationError("No processing backend available")

    async def _route_to_cloud(
        self,
        prompt: str,
        system_prompt: str | None,
        **kwargs: Any,
    ) -> Any:
        """Route request to cloud handler."""
        if not self.cloud_handler:
            raise PrivacyViolationError("No cloud handler configured")

        return await self.cloud_handler(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs,
        )

    def _record_decision(
        self,
        level: PrivacyLevel,
        backend: str,
        fallback_used: bool,
        reason: str,
        prompt: str,
    ) -> RoutingDecision:
        """Record routing decision for audit trail."""
        import hashlib

        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        decision = RoutingDecision(
            timestamp=datetime.now(),
            privacy_level=level,
            backend_used=backend,
            fallback_used=fallback_used,
            reason=reason,
            prompt_hash=prompt_hash,
        )

        if self.config.log_routing_decisions:
            logger.info(
                f"Privacy routing: {level.value} → {backend} "
                f"(fallback={fallback_used}): {reason}"
            )

        self._routing_history.append(decision)
        return decision

    def get_routing_history(
        self,
        limit: int = 100,
    ) -> list[RoutingDecision]:
        """Get recent routing decisions for audit.

        Args:
            limit: Maximum number of decisions to return.

        Returns:
            List of recent routing decisions.
        """
        return self._routing_history[-limit:]

    def get_routing_statistics(self) -> dict[str, Any]:
        """Get statistics about routing decisions.

        Returns:
            Dictionary with routing statistics.
        """
        total = len(self._routing_history)
        if total == 0:
            return {"total": 0}

        local_count = sum(1 for d in self._routing_history if d.backend_used == "local")
        cloud_count = sum(1 for d in self._routing_history if d.backend_used == "cloud")
        fallback_count = sum(1 for d in self._routing_history if d.fallback_used)

        by_level = {}
        for level in PrivacyLevel:
            by_level[level.value] = sum(
                1 for d in self._routing_history if d.privacy_level == level
            )

        return {
            "total": total,
            "local_count": local_count,
            "cloud_count": cloud_count,
            "fallback_count": fallback_count,
            "local_percentage": (local_count / total) * 100,
            "cloud_percentage": (cloud_count / total) * 100,
            "by_privacy_level": by_level,
        }

    async def chat_with_privacy(
        self,
        messages: list[ChatMessage],
        privacy_level: PrivacyLevel | None = None,
        model: OllamaModel | None = None,
    ) -> PrivacyRoutingResult:
        """Chat completion with privacy routing.

        Args:
            messages: Chat message history.
            privacy_level: Privacy level (auto-detected from messages if not provided).
            model: Ollama model to use.

        Returns:
            PrivacyRoutingResult with response.
        """
        # Combine all messages for sensitivity detection
        combined_text = " ".join(m.content for m in messages)
        level = privacy_level or self.detect_privacy_level(combined_text)

        if level.requires_local:
            if not await self.ollama.is_available():
                raise PrivacyViolationError(
                    "Local LLM required for privileged chat but Ollama unavailable"
                )

            response = await self.ollama.chat(messages, model=model)
            decision = self._record_decision(
                level,
                "local",
                False,
                "Chat processed locally",
                combined_text,
            )
            return PrivacyRoutingResult(
                backend="local",
                response=response,
                decision=decision,
            )

        # For non-privileged, try local first
        if await self.ollama.is_available():
            response = await self.ollama.chat(messages, model=model)
            decision = self._record_decision(
                level,
                "local",
                False,
                "Chat processed locally",
                combined_text,
            )
            return PrivacyRoutingResult(
                backend="local",
                response=response,
                decision=decision,
            )

        # Cloud fallback for confidential/public
        if level.allows_cloud and self.config.allow_cloud_fallback and self.cloud_handler:
            cloud_response = await self.cloud_handler(messages=messages)
            decision = self._record_decision(
                level,
                "cloud",
                True,
                "Chat fallback to cloud",
                combined_text,
            )
            return PrivacyRoutingResult(
                backend="cloud",
                response=None,
                decision=decision,
                cloud_response=cloud_response,
            )

        raise PrivacyViolationError("No suitable backend available for chat")
