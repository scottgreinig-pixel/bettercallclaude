# Agent Framework package
# v1.2.0 - StrategistAgent, DrafterAgent, Orchestration

from src.agents.base import (
    ActionType,
    AgentBase,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
    CaseContext,
    Checkpoint,
    Party,
)
from src.agents.drafter import (
    DrafterAgent,
)
from src.agents.models.drafter import (
    Citation,
    DocumentMetadata,
    DocumentSection,
    DocumentSectionType,
    DocumentType,
    LegalDocument,
)

# Re-export models for convenience
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
from src.agents.orchestrator import (
    AgentOrchestrator,
    OrchestrationStep,
    PipelineResult,
    PipelineStatus,
)
from src.agents.pipeline_builder import (
    ConditionalStep,
    ParallelGroup,
    Pipeline,
    PipelineBuilder,
    PipelineExecutionResult,
    PipelineExecutor,
    PipelineStep,
    RouterStep,
    StepType,
    create_full_case_pipeline,
    create_research_pipeline,
)
from src.agents.researcher import (
    LegalDomain,
    ResearchDepth,
    ResearcherAgent,
    SearchStrategy,
)
from src.agents.strategist import (
    StrategistAgent,
)

__all__ = [
    # Base classes
    "ActionType",
    "AgentBase",
    "AgentOutcome",
    "AgentResult",
    "AutonomyMode",
    "CaseContext",
    "Checkpoint",
    "Party",
    # Researcher
    "LegalDomain",
    "ResearchDepth",
    "ResearcherAgent",
    "SearchStrategy",
    # Strategist (NEW v1.2)
    "StrategistAgent",
    # Drafter (NEW v1.2)
    "DrafterAgent",
    # Orchestrator (NEW v1.2)
    "AgentOrchestrator",
    "OrchestrationStep",
    "PipelineResult",
    "PipelineStatus",
    # Pipeline Builder (NEW v2.0)
    "ConditionalStep",
    "ParallelGroup",
    "Pipeline",
    "PipelineBuilder",
    "PipelineExecutionResult",
    "PipelineExecutor",
    "PipelineStep",
    "RouterStep",
    "StepType",
    "create_full_case_pipeline",
    "create_research_pipeline",
    # Shared Models
    "CaseFacts",
    "Jurisdiction",
    "Language",
    "LegalParty",
    "RiskLevel",
    # Strategist Models
    "CostEstimate",
    "OpponentProfile",
    "RiskAssessment",
    "StrategyRecommendation",
    "StrategyType",
    "SuccessProbability",
    # Drafter Models
    "Citation",
    "DocumentMetadata",
    "DocumentSection",
    "DocumentSectionType",
    "DocumentType",
    "LegalDocument",
]
