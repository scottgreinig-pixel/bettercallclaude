"""
YAML-based data structures for agent communication.

Structures:
- UserQueryPackage: Input query with metadata (jurisdiction, language)
- AdvocateReport: Pro-position analysis with citations
- AdversaryReport: Anti-position analysis with citations
- JudicialReport: Objective synthesis with balanced assessment
"""

from adversarial_workflow.data_structures.user_query_package import (
    Jurisdiction,
    Language,
    Metadata,
    UserQueryPackage,
)

__all__ = [
    "UserQueryPackage",
    "Jurisdiction",
    "Language",
    "Metadata",
    "AdvocateReport",  # Not yet implemented
    "AdversaryReport",  # Not yet implemented
    "JudicialReport",  # Not yet implemented
]
