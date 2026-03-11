"""
MCP Server Adapters for BetterCallClaude v2.0

This package provides high-level adapters for Swiss legal data sources
that abstract the MCP protocol details and provide domain-specific interfaces.
"""

from .bge_search import BGESearchAdapter
from .cantonal_courts import CantonalCourtsAdapter
from .entscheidsuche import EntscheidausucheAdapter

__all__ = ["BGESearchAdapter", "EntscheidausucheAdapter", "CantonalCourtsAdapter"]
