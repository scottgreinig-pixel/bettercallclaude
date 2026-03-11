"""
11-state workflow state machine.

States:
IDLE → INITIALIZING → PARALLEL_RESEARCH → VALIDATING_REPORTS →
JUDICIAL_SYNTHESIS → VALIDATING_OBJECTIVITY → COMPLETED

Also handles ERROR and FAILED states for graceful degradation.
"""

__all__ = ["WorkflowStateMachine", "WorkflowState"]
