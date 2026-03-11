"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgentBase = exports.ActionType = exports.AgentOutcome = exports.AutonomyMode = void 0;
exports.createAction = createAction;
exports.createCheckpoint = createCheckpoint;
const uuid_1 = require("uuid");
// =============================================================================
// Enums and Types
// =============================================================================
/**
 * Autonomy levels controlling agent interaction with user.
 */
var AutonomyMode;
(function (AutonomyMode) {
    /** Confirms before each significant action */
    AutonomyMode["CAUTIOUS"] = "cautious";
    /** Confirms at key checkpoints only (default) */
    AutonomyMode["BALANCED"] = "balanced";
    /** Runs to completion with minimal interruption */
    AutonomyMode["AUTONOMOUS"] = "autonomous";
})(AutonomyMode || (exports.AutonomyMode = AutonomyMode = {}));
/**
 * Result status of agent execution.
 */
var AgentOutcome;
(function (AgentOutcome) {
    AgentOutcome["SUCCESS"] = "success";
    AgentOutcome["PARTIAL"] = "partial";
    AgentOutcome["FAILED"] = "failed";
    AgentOutcome["CANCELLED"] = "cancelled";
})(AgentOutcome || (exports.AgentOutcome = AgentOutcome = {}));
/**
 * Types of actions an agent can perform.
 */
var ActionType;
(function (ActionType) {
    ActionType["SEARCH"] = "search";
    ActionType["ANALYZE"] = "analyze";
    ActionType["GENERATE"] = "generate";
    ActionType["INVOKE_AGENT"] = "invoke_agent";
    ActionType["CHECKPOINT"] = "checkpoint";
    ActionType["USER_CONFIRM"] = "user_confirm";
})(ActionType || (exports.ActionType = ActionType = {}));
// =============================================================================
// Helper Functions
// =============================================================================
/**
 * Create a new AgentAction with auto-generated ID and timestamp.
 */
function createAction(actionType, description, inputs, outputs, durationMs, subAgentId) {
    return {
        actionId: (0, uuid_1.v4)(),
        timestamp: new Date(),
        actionType,
        description,
        inputs,
        outputs,
        durationMs,
        subAgentId,
    };
}
/**
 * Create a new Checkpoint.
 */
function createCheckpoint(checkpointType, state, description) {
    return {
        checkpointId: (0, uuid_1.v4)(),
        timestamp: new Date(),
        checkpointType,
        state,
        description,
    };
}
// =============================================================================
// Agent Base Class
// =============================================================================
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
class AgentBase {
    autonomyMode;
    caseContext;
    userId;
    firmId;
    // Execution state
    actions = [];
    checkpoints = [];
    sourcesAccessed = [];
    documentsRead = [];
    documentsWritten = [];
    errors = [];
    startTime;
    currentState = {};
    constructor(config = {}) {
        this.autonomyMode = config.autonomyMode ?? AutonomyMode.BALANCED;
        this.caseContext = config.caseContext;
        this.userId = config.userId ?? "anonymous";
        this.firmId = config.firmId ?? "default";
    }
    // ---------------------------------------------------------------------------
    // Checkpoint Management
    // ---------------------------------------------------------------------------
    /**
     * Create a checkpoint of current state.
     *
     * @param checkpointType - One of 'auto', 'user', 'pre_external', 'pre_subagent'
     * @param description - Human-readable description of the checkpoint
     * @returns The created Checkpoint object
     */
    createCheckpoint(checkpointType = "auto", description = "") {
        const checkpoint = createCheckpoint(checkpointType, { ...this.currentState }, description || `Checkpoint at ${new Date().toISOString()}`);
        this.checkpoints.push(checkpoint);
        // Log checkpoint action
        this.recordAction(ActionType.CHECKPOINT, `Created ${checkpointType} checkpoint`, {}, { checkpointId: checkpoint.checkpointId }, 0);
        console.log(`Checkpoint created: ${checkpoint.checkpointId}`);
        return checkpoint;
    }
    /**
     * Restore state from a checkpoint.
     *
     * @param checkpointId - ID of the checkpoint to restore
     * @returns True if restoration successful, False otherwise
     */
    restoreCheckpoint(checkpointId) {
        for (let i = this.checkpoints.length - 1; i >= 0; i--) {
            const cp = this.checkpoints[i];
            if (cp.checkpointId === checkpointId) {
                this.currentState = { ...cp.state };
                console.log(`Restored checkpoint: ${checkpointId}`);
                return true;
            }
        }
        console.warn(`Checkpoint not found: ${checkpointId}`);
        return false;
    }
    /**
     * Get the most recent checkpoint.
     */
    getLatestCheckpoint() {
        return this.checkpoints[this.checkpoints.length - 1];
    }
    // ---------------------------------------------------------------------------
    // Action Recording
    // ---------------------------------------------------------------------------
    /**
     * Record an action in the audit log.
     */
    recordAction(actionType, description, inputs, outputs, durationMs, subAgentId) {
        const action = createAction(actionType, description, this.sanitizeInputs(inputs), this.summarizeOutputs(outputs), durationMs, subAgentId);
        this.actions.push(action);
        return action;
    }
    /**
     * Sanitize inputs for audit logging.
     * Removes sensitive data and truncates large values.
     */
    sanitizeInputs(inputs) {
        const sanitized = {};
        const sensitiveKeys = ["password", "token", "secret", "key", "credential"];
        for (const [key, value] of Object.entries(inputs)) {
            if (sensitiveKeys.some((s) => key.toLowerCase().includes(s))) {
                sanitized[key] = "[REDACTED]";
            }
            else if (typeof value === "string" && value.length > 1000) {
                sanitized[key] = value.substring(0, 1000) + "...[truncated]";
            }
            else {
                sanitized[key] = value;
            }
        }
        return sanitized;
    }
    /**
     * Summarize outputs for audit logging.
     * Creates compact representation of large outputs.
     */
    summarizeOutputs(outputs) {
        const summarized = {};
        for (const [key, value] of Object.entries(outputs)) {
            if (Array.isArray(value)) {
                summarized[key] = `[List with ${value.length} items]`;
            }
            else if (typeof value === "object" && value !== null) {
                summarized[key] = `[Object with ${Object.keys(value).length} keys]`;
            }
            else if (typeof value === "string" && value.length > 500) {
                summarized[key] = value.substring(0, 500) + "...[truncated]";
            }
            else {
                summarized[key] = value;
            }
        }
        return summarized;
    }
    // ---------------------------------------------------------------------------
    // Sub-Agent Invocation
    // ---------------------------------------------------------------------------
    /**
     * Invoke a sub-agent with context inheritance.
     *
     * @param AgentClass - The agent class to instantiate
     * @param task - Task description for the sub-agent
     * @param autonomyOverride - Optional autonomy mode override
     * @param options - Additional parameters for the sub-agent
     * @returns AgentResult from the sub-agent
     */
    async invokeSubAgent(AgentClass, task, autonomyOverride, options) {
        // Create checkpoint before sub-agent invocation
        this.createCheckpoint("pre_subagent", `Before invoking ${AgentClass.name}`);
        // Inherit autonomy mode unless overridden
        const subAutonomy = autonomyOverride ?? this.autonomyMode;
        // Instantiate sub-agent with inherited context
        const subAgent = new AgentClass({
            autonomyMode: subAutonomy,
            caseContext: this.caseContext,
            userId: this.userId,
            firmId: this.firmId,
        });
        const start = Date.now();
        const result = await subAgent.execute(task, options);
        const durationMs = Date.now() - start;
        // Record the sub-agent invocation
        this.recordAction(ActionType.INVOKE_AGENT, `Invoked ${subAgent.agentId}`, { task, ...options }, { outcome: result.outcome }, durationMs, subAgent.agentId);
        return result;
    }
    // ---------------------------------------------------------------------------
    // User Interaction
    // ---------------------------------------------------------------------------
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
    async requestUserConfirmation(message, options = ["yes", "no"]) {
        if (this.autonomyMode === AutonomyMode.AUTONOMOUS) {
            return "yes";
        }
        // In real implementation, this would interact with the user
        console.log(`User confirmation requested: ${message}`);
        this.recordAction(ActionType.USER_CONFIRM, `Requested user confirmation: ${message}`, { message, options }, { response: "yes" }, 0);
        return "yes";
    }
    // ---------------------------------------------------------------------------
    // Audit Log Generation
    // ---------------------------------------------------------------------------
    /**
     * Generate complete audit log for the execution.
     */
    createAuditLog(outcome, deliverables) {
        return {
            logId: (0, uuid_1.v4)(),
            timestamp: this.startTime ?? new Date(),
            caseId: this.caseContext?.caseId ?? "no_case",
            userId: this.userId,
            firmId: this.firmId,
            agentId: this.agentId,
            agentVersion: this.agentVersion,
            autonomyMode: this.autonomyMode,
            actions: this.actions,
            sourcesAccessed: this.sourcesAccessed,
            documentsRead: this.documentsRead,
            documentsWritten: this.documentsWritten,
            outcome,
            deliverables,
            errors: this.errors,
            checkpoints: this.checkpoints,
        };
    }
    // ---------------------------------------------------------------------------
    // Error Handling
    // ---------------------------------------------------------------------------
    /**
     * Handle an error during execution.
     *
     * @param error - The error that occurred
     * @param recoverable - Whether execution can continue
     */
    handleError(error, recoverable = true) {
        const errorRecord = {
            type: error.name,
            message: error.message,
            timestamp: new Date().toISOString(),
            recoverable,
        };
        this.errors.push(errorRecord);
        console.error(`Agent error: ${error.message}`, error);
        if (recoverable) {
            // Escalate to cautious mode
            this.autonomyMode = AutonomyMode.CAUTIOUS;
            console.log("Escalated to cautious mode after error");
        }
    }
    /**
     * Create a partial result package when execution fails midway.
     */
    createPartialResult(partialData) {
        const latestCheckpoint = this.getLatestCheckpoint();
        return {
            partialData,
            checkpointId: latestCheckpoint?.checkpointId,
            actionsCompleted: this.actions.length,
            recoveredAt: new Date().toISOString(),
        };
    }
    // ---------------------------------------------------------------------------
    // Utility Methods
    // ---------------------------------------------------------------------------
    /**
     * Record access to an external source (for audit).
     */
    recordSourceAccess(source) {
        this.sourcesAccessed.push(source);
    }
    /**
     * Record reading a document (for audit).
     */
    recordDocumentRead(document) {
        this.documentsRead.push(document);
    }
    /**
     * Record writing a document (for audit).
     */
    recordDocumentWrite(document) {
        this.documentsWritten.push(document);
    }
    /**
     * Update internal state (included in checkpoints).
     */
    updateState(key, value) {
        this.currentState[key] = value;
    }
    /**
     * Get value from internal state.
     */
    getState(key, defaultValue) {
        return this.currentState[key] ?? defaultValue;
    }
    /**
     * Mark execution start time.
     */
    markStart() {
        this.startTime = new Date();
    }
    /**
     * Reset execution state for new run.
     */
    resetState() {
        this.actions = [];
        this.checkpoints = [];
        this.sourcesAccessed = [];
        this.documentsRead = [];
        this.documentsWritten = [];
        this.errors = [];
        this.startTime = undefined;
        this.currentState = {};
    }
}
exports.AgentBase = AgentBase;
//# sourceMappingURL=base.js.map