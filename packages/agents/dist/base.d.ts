/**
 * BetterCallClaude Agent Base Class (TypeScript)
 *
 * This module provides the foundational classes for building legal intelligence agents.
 * All agents inherit from AgentBase and implement the execute() method.
 *
 * Architecture:
 * - AgentBase: Core functionality (checkpoints, audit, sub-agent invocation)
 * - AutonomyMode: Enum for cautious/balanced/autonomous modes
 * - CaseContext: Shared context across agent executions
 * - AgentResult: Standardized result format
 */
/**
 * Autonomy levels controlling agent interaction with user.
 */
export declare enum AutonomyMode {
    /** Confirms before each significant action */
    CAUTIOUS = "cautious",
    /** Confirms at key checkpoints only (default) */
    BALANCED = "balanced",
    /** Runs to completion with minimal interruption */
    AUTONOMOUS = "autonomous"
}
/**
 * Result status of agent execution.
 */
export declare enum AgentOutcome {
    SUCCESS = "success",
    PARTIAL = "partial",
    FAILED = "failed",
    CANCELLED = "cancelled"
}
/**
 * Types of actions an agent can perform.
 */
export declare enum ActionType {
    SEARCH = "search",
    ANALYZE = "analyze",
    GENERATE = "generate",
    INVOKE_AGENT = "invoke_agent",
    CHECKPOINT = "checkpoint",
    USER_CONFIRM = "user_confirm"
}
/**
 * Represents a party in a legal case.
 */
export interface Party {
    name: string;
    role: string;
    contact?: string;
    metadata: Record<string, unknown>;
}
/**
 * Jurisdiction configuration for a case.
 */
export interface Jurisdiction {
    federal: boolean;
    cantons: string[];
    languages: ("DE" | "FR" | "IT" | "EN")[];
}
/**
 * Shared context for a legal case, inherited by all agents.
 */
export interface CaseContext {
    caseId: string;
    title: string;
    caseType: "litigation" | "corporate" | "contract" | "regulatory" | "other";
    jurisdiction: Jurisdiction;
    parties: Party[];
    facts: string[];
    legalIssues: string[];
    agentHistory: string[];
    findings: Record<string, unknown>;
    createdAt: Date;
}
/**
 * Records a single action taken by an agent.
 */
export interface AgentAction {
    actionId: string;
    timestamp: Date;
    actionType: ActionType;
    description: string;
    inputs: Record<string, unknown>;
    outputs: Record<string, unknown>;
    durationMs: number;
    subAgentId?: string;
}
/**
 * Snapshot of agent state for recovery.
 */
export interface Checkpoint {
    checkpointId: string;
    timestamp: Date;
    checkpointType: "auto" | "user" | "pre_external" | "pre_subagent";
    state: Record<string, unknown>;
    description: string;
}
/**
 * Complete audit trail for an agent execution.
 */
export interface AgentAuditLog {
    logId: string;
    timestamp: Date;
    caseId: string;
    userId: string;
    firmId: string;
    agentId: string;
    agentVersion: string;
    autonomyMode: AutonomyMode;
    actions: AgentAction[];
    sourcesAccessed: string[];
    documentsRead: string[];
    documentsWritten: string[];
    outcome: AgentOutcome;
    deliverables: string[];
    errors: ErrorRecord[];
    checkpoints: Checkpoint[];
}
/**
 * Error record for audit logging.
 */
export interface ErrorRecord {
    type: string;
    message: string;
    timestamp: string;
    recoverable: boolean;
}
/**
 * Standardized result format for agent execution.
 */
export interface AgentResult<T = unknown> {
    success: boolean;
    outcome: AgentOutcome;
    deliverable?: T;
    partialResults?: T;
    errorMessage?: string;
    auditLog: AgentAuditLog;
    executionTimeMs: number;
}
/**
 * Configuration options for agent instantiation.
 */
export interface AgentConfig {
    autonomyMode?: AutonomyMode;
    caseContext?: CaseContext;
    userId?: string;
    firmId?: string;
}
/**
 * Create a new AgentAction with auto-generated ID and timestamp.
 */
declare function createAction(actionType: ActionType, description: string, inputs: Record<string, unknown>, outputs: Record<string, unknown>, durationMs: number, subAgentId?: string): AgentAction;
/**
 * Create a new Checkpoint.
 */
declare function createCheckpoint(checkpointType: Checkpoint["checkpointType"], state: Record<string, unknown>, description: string): Checkpoint;
/**
 * Abstract base class for all BetterCallClaude agents.
 *
 * Provides core functionality:
 * - Autonomy mode management
 * - Checkpoint creation and recovery
 * - Audit logging
 * - Sub-agent invocation
 * - Case context handling
 *
 * Subclasses must implement:
 * - execute(): Main agent logic
 * - agentId: Unique identifier
 * - agentVersion: Version string
 */
export declare abstract class AgentBase {
    protected autonomyMode: AutonomyMode;
    protected caseContext?: CaseContext;
    protected userId: string;
    protected firmId: string;
    private actions;
    private checkpoints;
    private sourcesAccessed;
    private documentsRead;
    private documentsWritten;
    private errors;
    protected startTime?: Date;
    private currentState;
    constructor(config?: AgentConfig);
    /**
     * Unique identifier for this agent type (e.g., 'researcher').
     */
    abstract get agentId(): string;
    /**
     * Version string for this agent (e.g., '1.0.0').
     */
    abstract get agentVersion(): string;
    /**
     * Execute the agent's main task.
     *
     * @param task - Description of the task to perform
     * @param options - Additional task-specific parameters
     * @returns AgentResult with deliverable and audit information
     */
    abstract execute(task: string, options?: Record<string, unknown>): Promise<AgentResult>;
    /**
     * Create a checkpoint of current state.
     *
     * @param checkpointType - One of 'auto', 'user', 'pre_external', 'pre_subagent'
     * @param description - Human-readable description of the checkpoint
     * @returns The created Checkpoint object
     */
    protected createCheckpoint(checkpointType?: Checkpoint["checkpointType"], description?: string): Checkpoint;
    /**
     * Restore state from a checkpoint.
     *
     * @param checkpointId - ID of the checkpoint to restore
     * @returns True if restoration successful, False otherwise
     */
    protected restoreCheckpoint(checkpointId: string): boolean;
    /**
     * Get the most recent checkpoint.
     */
    protected getLatestCheckpoint(): Checkpoint | undefined;
    /**
     * Record an action in the audit log.
     */
    protected recordAction(actionType: ActionType, description: string, inputs: Record<string, unknown>, outputs: Record<string, unknown>, durationMs: number, subAgentId?: string): AgentAction;
    /**
     * Sanitize inputs for audit logging.
     * Removes sensitive data and truncates large values.
     */
    private sanitizeInputs;
    /**
     * Summarize outputs for audit logging.
     * Creates compact representation of large outputs.
     */
    private summarizeOutputs;
    /**
     * Invoke a sub-agent with context inheritance.
     *
     * @param AgentClass - The agent class to instantiate
     * @param task - Task description for the sub-agent
     * @param autonomyOverride - Optional autonomy mode override
     * @param options - Additional parameters for the sub-agent
     * @returns AgentResult from the sub-agent
     */
    protected invokeSubAgent<T extends AgentBase>(AgentClass: new (config: AgentConfig) => T, task: string, autonomyOverride?: AutonomyMode, options?: Record<string, unknown>): Promise<AgentResult>;
    /**
     * Request confirmation from user based on autonomy mode.
     *
     * In CAUTIOUS mode: Always requests
     * In BALANCED mode: Requests at checkpoints
     * In AUTONOMOUS mode: Skips (returns default)
     *
     * @param message - Message to show user
     * @param options - List of valid options (default: ["yes", "no"])
     * @returns User's response or "yes" in autonomous mode
     */
    protected requestUserConfirmation(message: string, options?: string[]): Promise<string>;
    /**
     * Generate complete audit log for the execution.
     */
    protected createAuditLog(outcome: AgentOutcome, deliverables: string[]): AgentAuditLog;
    /**
     * Handle an error during execution.
     *
     * @param error - The error that occurred
     * @param recoverable - Whether execution can continue
     */
    protected handleError(error: Error, recoverable?: boolean): void;
    /**
     * Create a partial result package when execution fails midway.
     */
    protected createPartialResult<T>(partialData: T): Record<string, unknown>;
    /**
     * Record access to an external source (for audit).
     */
    protected recordSourceAccess(source: string): void;
    /**
     * Record reading a document (for audit).
     */
    protected recordDocumentRead(document: string): void;
    /**
     * Record writing a document (for audit).
     */
    protected recordDocumentWrite(document: string): void;
    /**
     * Update internal state (included in checkpoints).
     */
    protected updateState(key: string, value: unknown): void;
    /**
     * Get value from internal state.
     */
    protected getState<T = unknown>(key: string, defaultValue?: T): T;
    /**
     * Mark execution start time.
     */
    protected markStart(): void;
    /**
     * Reset execution state for new run.
     */
    protected resetState(): void;
}
export { createAction, createCheckpoint, };
//# sourceMappingURL=base.d.ts.map