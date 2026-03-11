"""
BetterCallClaude Agent Models Package

This package contains shared data models for all agents in the framework.
Models are designed for Swiss legal context with multi-lingual support.

Modules:
- shared: Common enums and dataclasses (Language, Jurisdiction, RiskLevel, CaseFacts)
- strategist: StrategistAgent-specific models (StrategyType, RiskAssessment, CostEstimate)
- drafter: DrafterAgent-specific models (DocumentType, LegalDocument, DocumentSection)
"""

from src.agents.models.drafter import (
    DocumentMetadata,
    DocumentSection,
    DocumentSectionType,
    DocumentType,
    LegalDocument,
)
from src.agents.models.shared import (
    CaseFacts,
    Jurisdiction,
    Language,
    LegalParty,
    RiskLevel,
)
from src.agents.models.strategist import (
    CostEstimate,
    OpponentProfile,
    RiskAssessment,
    StrategyRecommendation,
    StrategyType,
    SuccessProbability,
)

__all__ = [
    # Shared models
    "Language",
    "RiskLevel",
    "Jurisdiction",
    "LegalParty",
    "CaseFacts",
    # Strategist models
    "StrategyType",
    "SuccessProbability",
    "RiskAssessment",
    "CostEstimate",
    "OpponentProfile",
    "StrategyRecommendation",
    # Drafter models
    "DocumentType",
    "DocumentSectionType",
    "DocumentMetadata",
    "DocumentSection",
    "LegalDocument",
]
