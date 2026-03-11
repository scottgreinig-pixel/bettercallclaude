/**
 * BetterCallClaude Researcher Agent (TypeScript)
 *
 * The foundational legal research agent that enables the 80% time savings target.
 * Performs deep, multi-source legal research with automatic citation verification.
 *
 * Workflow:
 * 1. UNDERSTAND - Parse question, identify legal issues
 * 2. PLAN - Determine search strategy
 * 3. SEARCH - Execute parallel searches across sources
 * 4. VERIFY - Verify citations via sub-agent
 * 5. SYNTHESIZE - Analyze findings, identify patterns
 * 6. DELIVER - Generate research memo
 */
import { AgentBase, AgentConfig, AgentResult } from "./base";
/**
 * Swiss legal domains for classification.
 */
export declare enum LegalDomain {
    CONTRACT = "contract",// Vertragsrecht (OR)
    TORT = "tort",// Haftpflichtrecht
    PROPERTY = "property",// Sachenrecht (ZGB)
    FAMILY = "family",// Familienrecht
    SUCCESSION = "succession",// Erbrecht
    CORPORATE = "corporate",// Gesellschaftsrecht
    EMPLOYMENT = "employment",// Arbeitsrecht
    CRIMINAL = "criminal",// Strafrecht (StGB)
    ADMINISTRATIVE = "administrative",// Verwaltungsrecht
    PROCEDURAL = "procedural",// Verfahrensrecht (ZPO, StPO)
    DEBT_COLLECTION = "debt_collection",// SchKG
    INTELLECTUAL_PROPERTY = "ip",// Immaterialgüterrecht
    OTHER = "other"
}
/**
 * Research depth levels.
 */
export declare enum ResearchDepth {
    QUICK = "quick",// 2 min, 10 sources
    STANDARD = "standard",// 5 min, 30 sources
    DEEP = "deep"
}
/**
 * Extracted parameters from research question.
 */
export interface ResearchParameters {
    originalQuestion: string;
    legalDomains: LegalDomain[];
    keyTerms: string[];
    concepts: string[];
    jurisdictionFederal: boolean;
    jurisdictionCantons: string[];
    timeRangeFrom?: Date;
    timeRangeTo?: Date;
    languages: string[];
    statuteReferences: string[];
}
/**
 * Configuration for a search source.
 */
export interface SearchSource {
    name: string;
    priority: number;
    expectedVolume: number;
    mcpServer: string;
    searchMethod: string;
}
/**
 * A single search query for a source.
 */
export interface SearchQuery {
    source: string;
    query: string;
    filters: Record<string, unknown>;
    language: string;
    maxResults: number;
}
/**
 * Complete search strategy.
 */
export interface SearchStrategy {
    sources: SearchSource[];
    queries: SearchQuery[];
    relevanceThreshold: number;
    maxTotalResults: number;
    parallelLimit: number;
}
/**
 * A single search result.
 */
export interface RawResult {
    id: string;
    title: string;
    citation: string;
    date?: Date;
    court: string;
    summary: string;
    relevanceScore: number;
    source: string;
    fullTextUrl?: string;
    language: string;
}
/**
 * Aggregated search results.
 */
export interface SearchResults {
    results: RawResult[];
    bySource: Record<string, RawResult[]>;
    totalFound: number;
    deduplicatedCount: number;
    processingTimeMs: number;
}
/**
 * A verified citation.
 */
export interface VerifiedCitation {
    citation: string;
    isValid: boolean;
    isCurrent: boolean;
    formatted: string;
    court: string;
    date?: Date;
    issues: string[];
}
/**
 * Citation verification report.
 */
export interface VerificationReport {
    verified: VerifiedCitation[];
    outdated: VerifiedCitation[];
    errors: Array<{
        citation: string;
        error: string;
    }>;
    overallAccuracy: number;
}
/**
 * A research finding.
 */
export interface ResearchFinding {
    issue: string;
    conclusion: string;
    supportingCitations: string[];
    confidence: number;
    conflicts: string[];
}
/**
 * Research synthesis.
 */
export interface Synthesis {
    keyFindings: ResearchFinding[];
    precedentChain: string[];
    conflicts: Array<Record<string, unknown>>;
    gaps: string[];
    recommendations: string[];
}
/**
 * Final research deliverable.
 */
export interface ResearchMemo {
    title: string;
    executiveSummary: string;
    methodology: string;
    findings: ResearchFinding[];
    citations: VerifiedCitation[];
    limitations: string[];
    nextSteps: string[];
    metadata: Record<string, unknown>;
}
/**
 * Options for research execution.
 */
export interface ResearchOptions {
    depth?: ResearchDepth | string;
    maxSources?: number;
    outputFormat?: "memo" | "bullets" | "json";
}
/**
 * Abstract MCP client for legal research servers.
 * In production, this would connect to actual MCP servers.
 */
export interface MCPClient {
    call(server: string, method: string, params: Record<string, unknown>): Promise<Record<string, unknown>>;
}
/**
 * Default mock MCP client for development.
 */
declare class MockMCPClient implements MCPClient {
    call(server: string, method: string, params: Record<string, unknown>): Promise<Record<string, unknown>>;
}
/**
 * Legal research agent for Swiss law.
 *
 * Performs deep, multi-source research with citation verification.
 * Implements the workflow defined in AGENT_RESEARCHER_SPEC.md.
 */
export declare class ResearcherAgent extends AgentBase {
    private static readonly SWISS_STATUTES;
    private static readonly SWISS_CANTONS;
    private static readonly DOMAIN_KEYWORDS;
    private mcpClient;
    constructor(config?: AgentConfig & {
        mcpClient?: MCPClient;
    });
    get agentId(): string;
    get agentVersion(): string;
    /**
     * Execute legal research workflow.
     */
    execute(task: string, options?: ResearchOptions): Promise<AgentResult<ResearchMemo>>;
    private parseDepth;
    private understand;
    private detectDomains;
    private extractKeyTerms;
    private extractStatuteReferences;
    private detectJurisdiction;
    private detectLanguages;
    private extractConcepts;
    private plan;
    private configureSources;
    private generateQueries;
    private confirmStrategy;
    private showStrategySummary;
    private search;
    private executeQuery;
    private getMcpServer;
    private parseResults;
    private deduplicateResults;
    private handleSearchError;
    private verify;
    private reportVerification;
    private synthesize;
    private groupByIssue;
    private generateFinding;
    private buildPrecedentChain;
    private identifyConflicts;
    private identifyGaps;
    private generateRecommendations;
    private deliver;
    private generateExecutiveSummary;
    private generateMethodology;
    private compileLimitations;
    private createSuccessResult;
    private createFailureResult;
}
export { MockMCPClient, };
//# sourceMappingURL=researcher.d.ts.map