"""
BetterCallClaude integrations module.

Provides integrations with external services:
- Ollama: Local LLM inference with privacy mode
- Databases: Swisslex, Weblaw (planned)
- Practice Management: bexio, Abacus, Kleos (planned)
"""

from src.integrations.ollama import (
    OllamaClient,
    OllamaConfig,
    OllamaModel,
    OllamaResponse,
    OllamaUnavailableError,
    PrivacyConfig,
    PrivacyLevel,
    PrivacyRouter,
    PrivacyViolationError,
)

__all__ = [
    # Ollama
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
