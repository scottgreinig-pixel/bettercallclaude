"use strict";
/**
 * BetterCallClaude Agent Integration Module
 *
 * Provides a unified API for integrating CaseManager with agents
 * and MCP adapters for streamlined legal research workflows.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.AutonomyMode = exports.IntegratedResearchSystem = void 0;
exports.createIntegratedSystem = createIntegratedSystem;
exports.quickResearch = quickResearch;
const case_manager_1 = require("./case-manager");
const researcher_1 = require("./researcher");
const mcp_adapter_1 = require("./mcp-adapter");
const base_1 = require("./base");
Object.defineProperty(exports, "AutonomyMode", { enumerable: true, get: function () { return base_1.AutonomyMode; } });
// =============================================================================
// IntegratedResearchSystem
// =============================================================================
/**
 * Integrated research system that combines CaseManager, ResearcherAgent,
 * and MCP adapters into a unified workflow.
 *
 * @example
 * ```typescript
 * // Create integrated system
 * const system = new IntegratedResearchSystem({
 *   mcpConfig: {
 *     entscheidsuchePath: './mcp-servers/entscheidsuche/dist/index.js',
 *     legalCitationsPath: './mcp-servers/legal-citations/dist/index.js',
 *   },
 * });
 *
 * // Initialize (connects to MCP servers)
 * await system.initialize();
 *
 * // Create a new case
 * const caseContext = await system.createCase({
 *   title: "Contract Dispute - ABC Corp",
 *   caseType: "contract",
 *   cantons: ["ZH"],
 *   languages: ["DE", "EN"],
 * });
 *
 * // Run research bound to the case
 * const result = await system.researchWithCase(
 *   "BGE precedents on contractual liability under Art. 97 OR",
 *   caseContext.caseId,
 *   { depth: "deep", addFindings: true }
 * );
 *
 * // Shutdown
 * await system.shutdown();
 * ```
 */
class IntegratedResearchSystem {
    config;
    caseManager;
    mcpAdapter;
    initialized = false;
    constructor(config = {}) {
        this.config = {
            defaultAutonomyMode: base_1.AutonomyMode.BALANCED,
            userId: "system",
            firmId: "default",
            ...config,
        };
        // Use provided storage or default JSONFileCaseStorage
        const storage = this.config.caseStorage ?? new case_manager_1.JSONFileCaseStorage();
        this.caseManager = new case_manager_1.CaseManager(storage);
        this.mcpAdapter = new mcp_adapter_1.MCPAdapter(this.config.mcpConfig);
    }
    // ---------------------------------------------------------------------------
    // Lifecycle
    // ---------------------------------------------------------------------------
    /**
     * Initialize the system by connecting to MCP servers.
     */
    async initialize() {
        if (this.initialized) {
            return;
        }
        try {
            await this.mcpAdapter.connect();
            this.initialized = true;
            console.log("IntegratedResearchSystem initialized successfully");
        }
        catch (error) {
            console.error("Failed to initialize IntegratedResearchSystem:", error);
            throw error;
        }
    }
    /**
     * Shutdown the system by disconnecting from MCP servers.
     */
    async shutdown() {
        if (!this.initialized) {
            return;
        }
        try {
            await this.mcpAdapter.disconnect();
            this.initialized = false;
            console.log("IntegratedResearchSystem shutdown successfully");
        }
        catch (error) {
            console.error("Error during shutdown:", error);
            throw error;
        }
    }
    /**
     * Check if the system is initialized.
     */
    isInitialized() {
        return this.initialized;
    }
    // ---------------------------------------------------------------------------
    // Case Management
    // ---------------------------------------------------------------------------
    /**
     * Create a new case.
     */
    async createCase(options) {
        return this.caseManager.createCase(options);
    }
    /**
     * Open an existing case.
     * @throws Error if case not found
     */
    async openCase(caseId) {
        const caseContext = await this.caseManager.openCase(caseId);
        if (!caseContext) {
            throw new Error(`Case not found: ${caseId}`);
        }
        return caseContext;
    }
    /**
     * Get the currently open case.
     */
    get currentCase() {
        return this.caseManager.currentCase;
    }
    /**
     * Convert managed case context to agent-compatible context.
     */
    toAgentContext(managed) {
        return this.caseManager.toAgentContext(managed);
    }
    // ---------------------------------------------------------------------------
    // Research Operations
    // ---------------------------------------------------------------------------
    /**
     * Run research without case binding.
     * Useful for standalone research queries.
     */
    async research(task, options = {}) {
        this.ensureInitialized();
        const agent = new researcher_1.ResearcherAgent({
            autonomyMode: this.config.defaultAutonomyMode,
            userId: this.config.userId,
            firmId: this.config.firmId,
            mcpClient: this.mcpAdapter,
        });
        return agent.execute(task, options);
    }
    /**
     * Run research bound to a specific case.
     * Optionally records execution and adds findings to the case.
     */
    async researchWithCase(task, caseId, options = {}) {
        this.ensureInitialized();
        // Open the case
        const caseContext = await this.openCase(caseId);
        const agentContext = this.toAgentContext(caseContext);
        // Execute research
        const agent = new researcher_1.ResearcherAgent({
            autonomyMode: options.autonomyMode ?? this.config.defaultAutonomyMode,
            caseContext: agentContext,
            userId: this.config.userId,
            firmId: this.config.firmId,
            mcpClient: this.mcpAdapter,
        });
        const result = await agent.execute(task, options);
        let executionRecorded = false;
        let findingsAdded = false;
        // Record execution if requested
        if (options.recordExecution !== false) {
            await this.caseManager.recordAgentExecution(caseId, {
                agentId: agent.agentId,
                task,
                outcome: result.outcome,
                summary: result.success
                    ? `Completed research: ${task}`
                    : `Failed research: ${result.errorMessage ?? "Unknown error"}`,
                durationMs: result.executionTimeMs,
                deliverables: result.success ? ["research_memo"] : [],
            });
            executionRecorded = true;
        }
        // Add findings if requested and research succeeded
        if (options.addFindings !== false && result.success && result.deliverable) {
            const memo = result.deliverable;
            for (const finding of memo.findings) {
                await this.caseManager.addFinding(caseId, {
                    content: finding.conclusion,
                    source: `ResearcherAgent: ${task}`,
                    category: finding.issue,
                    confidence: finding.confidence,
                    citations: finding.supportingCitations,
                    agentId: agent.agentId,
                });
            }
            findingsAdded = true;
        }
        // Get updated case context
        const updatedContext = await this.openCase(caseId);
        return {
            result,
            caseContext: updatedContext,
            executionRecorded,
            findingsAdded,
        };
    }
    /**
     * Run research on the currently open case.
     */
    async researchCurrentCase(task, options = {}) {
        const current = this.currentCase;
        if (!current) {
            throw new Error("No case is currently open");
        }
        return this.researchWithCase(task, current.caseId, options);
    }
    // ---------------------------------------------------------------------------
    // Utility Methods
    // ---------------------------------------------------------------------------
    /**
     * Get the MCP adapter for direct access if needed.
     */
    getMCPAdapter() {
        return this.mcpAdapter;
    }
    /**
     * Get the case manager for direct access if needed.
     */
    getCaseManager() {
        return this.caseManager;
    }
    /**
     * Create a standalone ResearcherAgent with the system's MCP adapter.
     */
    createResearcherAgent(config) {
        this.ensureInitialized();
        return new researcher_1.ResearcherAgent({
            autonomyMode: config?.autonomyMode ?? this.config.defaultAutonomyMode,
            caseContext: config?.caseContext,
            userId: config?.userId ?? this.config.userId,
            firmId: config?.firmId ?? this.config.firmId,
            mcpClient: this.mcpAdapter,
        });
    }
    // ---------------------------------------------------------------------------
    // Private Helpers
    // ---------------------------------------------------------------------------
    ensureInitialized() {
        if (!this.initialized) {
            throw new Error("IntegratedResearchSystem not initialized. Call initialize() first.");
        }
    }
}
exports.IntegratedResearchSystem = IntegratedResearchSystem;
// =============================================================================
// Factory Functions
// =============================================================================
/**
 * Create and initialize an integrated research system.
 */
async function createIntegratedSystem(config) {
    const system = new IntegratedResearchSystem(config);
    await system.initialize();
    return system;
}
/**
 * Quick research function for standalone queries.
 * Creates a temporary system, runs research, and shuts down.
 */
async function quickResearch(task, options = {}) {
    const { mcpConfig, ...researchOptions } = options;
    const system = await createIntegratedSystem({ mcpConfig });
    try {
        return await system.research(task, researchOptions);
    }
    finally {
        await system.shutdown();
    }
}
//# sourceMappingURL=integration.js.map