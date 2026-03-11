# Agent utilities package
# Contains language detection and other helper functions

from src.agents.utils.language import (
    detect_language,
    detect_language_confidence,
    get_legal_terminology,
)

__all__ = [
    "detect_language",
    "detect_language_confidence",
    "get_legal_terminology",
]
