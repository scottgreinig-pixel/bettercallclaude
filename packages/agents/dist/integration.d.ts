/**
 * BetterCallClaude Agent Integration Module
 *
 * Provides a unified API for integrating CaseManager with agents
 * and MCP adapters for streamlined legal research workflows.
 */
import { CaseManager, ManagedCaseContext, CreateCaseOptions, CaseStorage } from "./case-manager";
import { ResearcherAgent, ResearchMemo, ResearchOptions } from "./researcher";
import { MCPAdapter, MCPAdapterConfig } from "./mcp-adapter";
import { AgentConfig, AgentResult, AutonomyMode, CaseContext } from "./base";
/**
 * Configuration for the integrated research system
 */
export interface IntegrationConfig {
    /** Case storage implementation (defaults to JSONFileCaseStorage) */
    caseStorage?: CaseStorage;
    /** MCP adapter configuration */
    mcpConfig?: MCPAdapterConfig;
    /** Default autonomy mode for agents */
    defaultAutonomyMode?: AutonomyMode;
    /** Default user ID */
    userId?: string;
    /** Default firm ID */
    firmId?: string;
}
/**
 * Options for case-bound research
 */
export interface CaseBoundResearchOptions extends ResearchOptions {
    /** Record agent execution in case history */
    recordExecution?: boolean;
    /** Add findings to case record */
    addFindings?: boolean;
    /** Custom autonomy mode for this research */
    autonomyMode?: AutonomyMode;
}
/**
 * Result of case-bound research
 */
export interface CaseBoundResearchResult {
    /** The research result */
    result: AgentResult<ResearchMemo>;
    /** The case context after research */
    caseContext: ManagedCaseContext;
    /** Whether execution was recorded */
    executionRecorded: boolean;
    /** Whether findings were added */
    findingsAdded: boolean;
}
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
export declare class IntegratedResearchSystem {
    private config;
    private caseManager;
    private mcpAdapter;
    private initialized;
    constructor(config?: IntegrationConfig);
    /**
     * Initialize the system by connecting to MCP servers.
     */
    initialize(): Promise<void>;
    /**
     * Shutdown the system by disconnecting from MCP servers.
     */
    shutdown(): Promise<void>;
    /**
     * Check if the system is initialized.
     */
    isInitialized(): boolean;
    /**
     * Create a new case.
     */
    createCase(options: CreateCaseOptions): Promise<ManagedCaseContext>;
    /**
     * Open an existing case.
     * @throws Error if case not found
     */
    openCase(caseId: string): Promise<ManagedCaseContext>;
    /**
     * Get the currently open case.
     */
    get currentCase(): ManagedCaseContext | null;
    /**
     * Convert managed case context to agent-compatible context.
     */
    toAgentContext(managed: ManagedCaseContext): CaseContext;
    /**
     * Run research without case binding.
     * Useful for standalone research queries.
     */
    research(task: string, options?: ResearchOptions): Promise<AgentResult<ResearchMemo>>;
    /**
     * Run research bound to a specific case.
     * Optionally records execution and adds findings to the case.
     */
    researchWithCase(task: string, caseId: string, options?: CaseBoundResearchOptions): Promise<CaseBoundResearchResult>;
    /**
     * Run research on the currently open case.
     */
    researchCurrentCase(task: string, options?: CaseBoundResearchOptions): Promise<CaseBoundResearchResult>;
    /**
     * Get the MCP adapter for direct access if needed.
     */
    getMCPAdapter(): MCPAdapter;
    /**
     * Get the case manager for direct access if needed.
     */
    getCaseManager(): CaseManager;
    /**
     * Create a standalone ResearcherAgent with the system's MCP adapter.
     */
    createResearcherAgent(config?: Partial<AgentConfig>): ResearcherAgent;
    private ensureInitialized;
}
/**
 * Create and initialize an integrated research system.
 */
export declare function createIntegratedSystem(config?: IntegrationConfig): Promise<IntegratedResearchSystem>;
/**
 * Quick research function for standalone queries.
 * Creates a temporary system, runs research, and shuts down.
 */
export declare function quickResearch(task: string, options?: ResearchOptions & {
    mcpConfig?: MCPAdapterConfig;
}): Promise<AgentResult<ResearchMemo>>;
export { AutonomyMode };
//# sourceMappingURL=integration.d.ts.map