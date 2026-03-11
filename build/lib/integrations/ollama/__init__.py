"""
Ollama integration for local LLM inference.

Provides privacy-first AI capabilities for sensitive legal work,
with graceful fallback to Claude when needed.
"""

from src.integrations.ollama.client import (
    OllamaClient,
    OllamaConfig,
    OllamaModel,
    OllamaResponse,
    OllamaUnavailableError,
)
from src.integrations.ollama.privacy_mode import (
    PrivacyConfig,
    PrivacyLevel,
    PrivacyRouter,
    PrivacyViolationError,
)

__all__ = [
    # Client
    "OllamaClient",
    "OllamaConfig",
    "OllamaModel",
    "OllamaResponse",
    "OllamaUnavailableError",
    # Privacy
    "PrivacyLevel",
    "PrivacyConfig",
    "PrivacyRouter",
    "PrivacyViolationError",
]
