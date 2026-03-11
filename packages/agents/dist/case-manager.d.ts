/**
 * BetterCallClaude Case Management System (TypeScript)
 *
 * Provides case lifecycle management with persistence:
 * - Case creation, opening, closing, archiving
 * - Context management for agent executions
 * - Findings, parties, deadlines, documents tracking
 * - Export functionality (JSON, Markdown)
 *
 * Swiss Legal Context:
 * - Federal and cantonal jurisdiction support
 * - Multi-language support (DE, FR, IT, EN)
 * - Legal domain awareness (OR, ZGB, StGB, etc.)
 */
import type { CaseContext, Party } from "./base";
/**
 * Case status lifecycle states.
 */
export declare enum CaseStatus {
    ACTIVE = "active",
    PAUSED = "paused",
    CLOSED = "closed",
    ARCHIVED = "archived"
}
/**
 * Types of legal cases.
 */
export declare enum CaseType {
    LITIGATION = "litigation",
    CORPORATE = "corporate",
    CONTRACT = "contract",
    REGULATORY = "regulatory",
    OTHER = "other"
}
/**
 * Legal areas in Swiss law.
 */
export declare enum LegalArea {
    OR = "or",// Obligationenrecht
    ZGB = "zgb",// Zivilgesetzbuch
    STGB = "stgb",// Strafgesetzbuch
    ZPO = "zpo",// Zivilprozessordnung
    STPO = "stpo",// Strafprozessordnung
    SCHKG = "schkg",// Schuldbetreibungs- und Konkursgesetz
    VWG = "vwg",// Verwaltungsverfahren
    OTHER = "other"
}
/**
 * Swiss cantons.
 */
export declare const SWISS_CANTONS: readonly ["ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG", "TI", "VD", "VS", "NE", "GE", "JU"];
export type SwissCanton = (typeof SWISS_CANTONS)[number];
/**
 * Extended party information.
 */
export interface ManagedParty extends Party {
    partyId: string;
    addedAt: Date;
}
/**
 * Deadline tracking.
 */
export interface Deadline {
    deadlineId: string;
    name: string;
    dueDate: Date;
    description: string;
    completed: boolean;
    completedAt?: Date;
    createdAt: Date;
}
/**
 * Milestone tracking.
 */
export interface Milestone {
    milestoneId: string;
    name: string;
    date: Date;
    description: string;
    createdAt: Date;
}
/**
 * Legal issue tracking.
 */
export interface LegalIssue {
    issueId: string;
    description: string;
    legalArea: LegalArea;
    relevantArticles: string[];
    status: "open" | "resolved" | "pending";
    notes: string;
    createdAt: Date;
    resolvedAt?: Date;
}
/**
 * Agent execution record.
 */
export interface AgentExecution {
    executionId: string;
    agentId: string;
    timestamp: Date;
    task: string;
    outcome: "success" | "partial" | "failed" | "cancelled";
    summary: string;
    durationMs: number;
    deliverables: string[];
}
/**
 * Finding from research or analysis.
 */
export interface Finding {
    findingId: string;
    content: string;
    source: string;
    timestamp: Date;
    category: string;
    confidence: number;
    citations: string[];
    agentId?: string;
}
/**
 * Document reference.
 */
export interface DocumentRef {
    documentId: string;
    name: string;
    path: string;
    documentType: string;
    addedAt: Date;
    metadata: Record<string, unknown>;
}
/**
 * Full managed case context with all lifecycle fields.
 */
export interface ManagedCaseContext extends CaseContext {
    status: CaseStatus;
    firmId: string;
    userId: string;
    managedParties: ManagedParty[];
    deadlines: Deadline[];
    milestones: Milestone[];
    managedLegalIssues: LegalIssue[];
    agentExecutions: AgentExecution[];
    managedFindings: Finding[];
    documents: DocumentRef[];
    createdBy: string;
    updatedAt: Date;
    closedAt?: Date;
    closureReason?: string;
    archivedAt?: Date;
    workingLanguages: ("DE" | "FR" | "IT" | "EN")[];
}
/**
 * Options for creating a new case.
 */
export interface CreateCaseOptions {
    title: string;
    caseType?: CaseType;
    jurisdictionFederal?: boolean;
    jurisdictionCantons?: SwissCanton[];
    languages?: ("DE" | "FR" | "IT" | "EN")[];
    parties?: Party[];
    userId?: string;
    firmId?: string;
}
/**
 * Case listing filters.
 */
export interface ListCasesOptions {
    firmId?: string;
    status?: CaseStatus;
    limit?: number;
    offset?: number;
}
/**
 * Case summary data.
 */
export interface CaseSummary {
    caseId: string;
    title: string;
    status: CaseStatus;
    caseType: CaseType;
    partiesCount: number;
    factsCount: number;
    findingsCount: number;
    openIssuesCount: number;
    upcomingDeadlines: Deadline[];
    recentAgentExecutions: AgentExecution[];
    createdAt: Date;
    updatedAt: Date;
}
/**
 * Abstract storage backend for cases.
 */
export interface CaseStorage {
    saveCase(caseId: string, data: ManagedCaseContext): Promise<boolean>;
    loadCase(caseId: string): Promise<ManagedCaseContext | null>;
    deleteCase(caseId: string): Promise<boolean>;
    listCases(options: ListCasesOptions): Promise<CaseIndexEntry[]>;
    caseExists(caseId: string): Promise<boolean>;
}
/**
 * Index entry for case listing.
 */
export interface CaseIndexEntry {
    caseId: string;
    title: string;
    caseType: string;
    status: string;
    firmId: string;
    createdAt: string;
    updatedAt: string;
}
/**
 * JSON file-based case storage.
 *
 * Stores each case as a separate JSON file with an index for fast listing.
 */
export declare class JSONFileCaseStorage implements CaseStorage {
    private storageDir;
    private indexFile;
    constructor(storageDir?: string);
    private ensureStorageDir;
    private getCaseFile;
    private loadIndex;
    private saveIndex;
    saveCase(caseId: string, data: ManagedCaseContext): Promise<boolean>;
    loadCase(caseId: string): Promise<ManagedCaseContext | null>;
    deleteCase(caseId: string): Promise<boolean>;
    listCases(options: ListCasesOptions): Promise<CaseIndexEntry[]>;
    caseExists(caseId: string): Promise<boolean>;
}
/**
 * Central case management class.
 *
 * Manages case lifecycle:
 * - Creation with jurisdiction and party setup
 * - Opening and context loading
 * - Updates (parties, facts, deadlines, findings)
 * - Closing and archiving
 * - Summary generation and export
 */
export declare class CaseManager {
    private storage;
    private _currentCase;
    constructor(storage?: CaseStorage);
    /**
     * Get the currently active case.
     */
    get currentCase(): ManagedCaseContext | null;
    /**
     * Generate a unique case ID.
     */
    private generateCaseId;
    /**
     * Create a new case.
     */
    createCase(options: CreateCaseOptions): Promise<ManagedCaseContext>;
    /**
     * Open an existing case.
     */
    openCase(caseId: string): Promise<ManagedCaseContext | null>;
    /**
     * Close a case.
     */
    closeCase(caseId?: string, reason?: string): Promise<boolean>;
    /**
     * Archive a case.
     */
    archiveCase(caseId?: string): Promise<boolean>;
    /**
     * List cases with filtering.
     */
    listCases(options?: ListCasesOptions): Promise<CaseIndexEntry[]>;
    /**
     * Add a party to a case.
     */
    addParty(caseId: string | undefined, party: Party): Promise<boolean>;
    /**
     * Add a fact to a case.
     */
    addFact(caseId: string | undefined, fact: string): Promise<boolean>;
    /**
     * Add a deadline to a case.
     */
    addDeadline(caseId: string | undefined, deadline: Omit<Deadline, "deadlineId" | "completed" | "createdAt">): Promise<boolean>;
    /**
     * Add a finding to a case.
     */
    addFinding(caseId: string | undefined, finding: Omit<Finding, "findingId" | "timestamp">): Promise<boolean>;
    /**
     * Add a document reference to a case.
     */
    addDocument(caseId: string | undefined, document: Omit<DocumentRef, "documentId" | "addedAt">): Promise<boolean>;
    /**
     * Record an agent execution.
     */
    recordAgentExecution(caseId: string | undefined, execution: Omit<AgentExecution, "executionId" | "timestamp">): Promise<boolean>;
    /**
     * Generate a case summary.
     */
    generateSummary(caseId?: string): Promise<CaseSummary | null>;
    /**
     * Export case data.
     */
    exportCase(caseId?: string, format?: "json" | "markdown"): Promise<string | null>;
    /**
     * Export case as Markdown.
     */
    private exportAsMarkdown;
    /**
     * Get the target case (specified or current).
     */
    private getTargetCase;
    /**
     * Convert ManagedCaseContext to simple CaseContext for agents.
     */
    toAgentContext(managed: ManagedCaseContext): CaseContext;
}
export default CaseManager;
//# sourceMappingURL=case-manager.d.ts.map