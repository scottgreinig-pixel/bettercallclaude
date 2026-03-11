"""
Adversarial Workflow System for BetterCallClaude v2.1.0

This module implements a three-agent adversarial workflow for Swiss legal analysis:
- Advocate Agent: Develops pro-position arguments
- Adversary Agent: Develops anti-position arguments
- Judicial Agent: Synthesizes objective analysis

The workflow follows an 11-state state machine with parallel research,
quality gates, and objectivity validation.
"""

__version__ = "2.1.0"
__all__ = [
    "agents",
    "data_structures",
    "quality_gates",
    "state_machine",
    "utils",
]
