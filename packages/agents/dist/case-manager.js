"use strict";
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
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.CaseManager = exports.JSONFileCaseStorage = exports.SWISS_CANTONS = exports.LegalArea = exports.CaseType = exports.CaseStatus = void 0;
const uuid_1 = require("uuid");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
// =============================================================================
// Enums and Constants
// =============================================================================
/**
 * Case status lifecycle states.
 */
var CaseStatus;
(function (CaseStatus) {
    CaseStatus["ACTIVE"] = "active";
    CaseStatus["PAUSED"] = "paused";
    CaseStatus["CLOSED"] = "closed";
    CaseStatus["ARCHIVED"] = "archived";
})(CaseStatus || (exports.CaseStatus = CaseStatus = {}));
/**
 * Types of legal cases.
 */
var CaseType;
(function (CaseType) {
    CaseType["LITIGATION"] = "litigation";
    CaseType["CORPORATE"] = "corporate";
    CaseType["CONTRACT"] = "contract";
    CaseType["REGULATORY"] = "regulatory";
    CaseType["OTHER"] = "other";
})(CaseType || (exports.CaseType = CaseType = {}));
/**
 * Legal areas in Swiss law.
 */
var LegalArea;
(function (LegalArea) {
    LegalArea["OR"] = "or";
    LegalArea["ZGB"] = "zgb";
    LegalArea["STGB"] = "stgb";
    LegalArea["ZPO"] = "zpo";
    LegalArea["STPO"] = "stpo";
    LegalArea["SCHKG"] = "schkg";
    LegalArea["VWG"] = "vwg";
    LegalArea["OTHER"] = "other";
})(LegalArea || (exports.LegalArea = LegalArea = {}));
/**
 * Swiss cantons.
 */
exports.SWISS_CANTONS = [
    "ZH",
    "BE",
    "LU",
    "UR",
    "SZ",
    "OW",
    "NW",
    "GL",
    "ZG",
    "FR",
    "SO",
    "BS",
    "BL",
    "SH",
    "AR",
    "AI",
    "SG",
    "GR",
    "AG",
    "TG",
    "TI",
    "VD",
    "VS",
    "NE",
    "GE",
    "JU",
];
// =============================================================================
// JSON File Storage Implementation
// =============================================================================
/**
 * JSON file-based case storage.
 *
 * Stores each case as a separate JSON file with an index for fast listing.
 */
class JSONFileCaseStorage {
    storageDir;
    indexFile;
    constructor(storageDir = ".bettercallclaude/cases") {
        this.storageDir = path.resolve(storageDir);
        this.indexFile = path.join(this.storageDir, "index.json");
        this.ensureStorageDir();
    }
    ensureStorageDir() {
        if (!fs.existsSync(this.storageDir)) {
            fs.mkdirSync(this.storageDir, { recursive: true });
        }
        if (!fs.existsSync(this.indexFile)) {
            this.saveIndex({});
        }
    }
    getCaseFile(caseId) {
        const safeId = caseId.replace(/[^a-zA-Z0-9-_]/g, "_");
        return path.join(this.storageDir, `${safeId}.json`);
    }
    loadIndex() {
        try {
            if (fs.existsSync(this.indexFile)) {
                const content = fs.readFileSync(this.indexFile, "utf-8");
                return JSON.parse(content);
            }
        }
        catch (error) {
            console.error("Failed to load case index:", error);
        }
        return {};
    }
    saveIndex(index) {
        try {
            fs.writeFileSync(this.indexFile, JSON.stringify(index, null, 2), "utf-8");
        }
        catch (error) {
            console.error("Failed to save case index:", error);
        }
    }
    async saveCase(caseId, data) {
        try {
            const caseFile = this.getCaseFile(caseId);
            // Save full case data
            fs.writeFileSync(caseFile, JSON.stringify(data, null, 2), "utf-8");
            // Update index
            const index = this.loadIndex();
            index[caseId] = {
                caseId,
                title: data.title,
                caseType: data.caseType,
                status: data.status,
                firmId: data.firmId,
                createdAt: data.createdAt.toISOString(),
                updatedAt: data.updatedAt.toISOString(),
            };
            this.saveIndex(index);
            console.log(`Saved case ${caseId} to ${caseFile}`);
            return true;
        }
        catch (error) {
            console.error(`Failed to save case ${caseId}:`, error);
            return false;
        }
    }
    async loadCase(caseId) {
        try {
            const caseFile = this.getCaseFile(caseId);
            if (!fs.existsSync(caseFile)) {
                console.warn(`Case file not found: ${caseFile}`);
                return null;
            }
            const content = fs.readFileSync(caseFile, "utf-8");
            const data = JSON.parse(content);
            // Convert date strings back to Date objects
            data.createdAt = new Date(data.createdAt);
            data.updatedAt = new Date(data.updatedAt);
            if (data.closedAt)
                data.closedAt = new Date(data.closedAt);
            if (data.archivedAt)
                data.archivedAt = new Date(data.archivedAt);
            console.log(`Loaded case ${caseId} from ${caseFile}`);
            return data;
        }
        catch (error) {
            console.error(`Failed to load case ${caseId}:`, error);
            return null;
        }
    }
    async deleteCase(caseId) {
        try {
            const caseFile = this.getCaseFile(caseId);
            if (fs.existsSync(caseFile)) {
                fs.unlinkSync(caseFile);
            }
            // Remove from index
            const index = this.loadIndex();
            if (index[caseId]) {
                delete index[caseId];
                this.saveIndex(index);
            }
            console.log(`Deleted case ${caseId}`);
            return true;
        }
        catch (error) {
            console.error(`Failed to delete case ${caseId}:`, error);
            return false;
        }
    }
    async listCases(options) {
        const index = this.loadIndex();
        let cases = Object.values(index);
        // Apply filters
        if (options.firmId) {
            cases = cases.filter((c) => c.firmId === options.firmId);
        }
        if (options.status) {
            cases = cases.filter((c) => c.status === options.status);
        }
        // Sort by updatedAt descending
        cases.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
        // Apply pagination
        const offset = options.offset ?? 0;
        const limit = options.limit ?? 100;
        return cases.slice(offset, offset + limit);
    }
    async caseExists(caseId) {
        const caseFile = this.getCaseFile(caseId);
        return fs.existsSync(caseFile);
    }
}
exports.JSONFileCaseStorage = JSONFileCaseStorage;
// =============================================================================
// Case Manager
// =============================================================================
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
class CaseManager {
    storage;
    _currentCase = null;
    constructor(storage) {
        this.storage = storage ?? new JSONFileCaseStorage();
    }
    /**
     * Get the currently active case.
     */
    get currentCase() {
        return this._currentCase;
    }
    /**
     * Generate a unique case ID.
     */
    generateCaseId(title) {
        const prefix = title
            .substring(0, 3)
            .toUpperCase()
            .replace(/[^A-Z]/g, "X");
        const year = new Date().getFullYear();
        const suffix = (0, uuid_1.v4)().substring(0, 4).toUpperCase();
        return `${prefix}-${year}-${suffix}`;
    }
    /**
     * Create a new case.
     */
    async createCase(options) {
        const caseId = this.generateCaseId(options.title);
        const now = new Date();
        const jurisdiction = {
            federal: options.jurisdictionFederal ?? true,
            cantons: options.jurisdictionCantons ?? [],
            languages: options.languages ?? ["DE"],
        };
        // Convert parties to managed parties
        const managedParties = (options.parties ?? []).map((p) => ({
            ...p,
            partyId: (0, uuid_1.v4)(),
            addedAt: now,
        }));
        const newCase = {
            caseId,
            title: options.title,
            caseType: options.caseType ?? CaseType.OTHER,
            jurisdiction,
            parties: options.parties ?? [],
            facts: [],
            legalIssues: [],
            agentHistory: [],
            findings: {},
            createdAt: now,
            status: CaseStatus.ACTIVE,
            firmId: options.firmId ?? "default",
            userId: options.userId ?? "anonymous",
            managedParties,
            deadlines: [],
            milestones: [],
            managedLegalIssues: [],
            agentExecutions: [],
            managedFindings: [],
            documents: [],
            createdBy: options.userId ?? "anonymous",
            updatedAt: now,
            workingLanguages: options.languages ?? ["DE"],
        };
        await this.storage.saveCase(caseId, newCase);
        this._currentCase = newCase;
        console.log(`Created case: ${caseId} - ${options.title}`);
        return newCase;
    }
    /**
     * Open an existing case.
     */
    async openCase(caseId) {
        const caseData = await this.storage.loadCase(caseId);
        if (caseData) {
            this._currentCase = caseData;
            console.log(`Opened case: ${caseId} - ${caseData.title}`);
        }
        return caseData;
    }
    /**
     * Close a case.
     */
    async closeCase(caseId, reason) {
        const targetId = caseId ?? this._currentCase?.caseId;
        if (!targetId) {
            console.error("No case specified and no current case active");
            return false;
        }
        const caseData = await this.storage.loadCase(targetId);
        if (!caseData) {
            console.error(`Case not found: ${targetId}`);
            return false;
        }
        caseData.status = CaseStatus.CLOSED;
        caseData.closedAt = new Date();
        caseData.closureReason = reason ?? "";
        caseData.updatedAt = new Date();
        const saved = await this.storage.saveCase(targetId, caseData);
        if (this._currentCase?.caseId === targetId) {
            this._currentCase = null;
        }
        console.log(`Closed case: ${targetId}`);
        return saved;
    }
    /**
     * Archive a case.
     */
    async archiveCase(caseId) {
        const targetId = caseId ?? this._currentCase?.caseId;
        if (!targetId) {
            return false;
        }
        const caseData = await this.storage.loadCase(targetId);
        if (!caseData) {
            return false;
        }
        caseData.status = CaseStatus.ARCHIVED;
        caseData.archivedAt = new Date();
        caseData.updatedAt = new Date();
        const saved = await this.storage.saveCase(targetId, caseData);
        if (this._currentCase?.caseId === targetId) {
            this._currentCase = null;
        }
        console.log(`Archived case: ${targetId}`);
        return saved;
    }
    /**
     * List cases with filtering.
     */
    async listCases(options = {}) {
        return this.storage.listCases(options);
    }
    /**
     * Add a party to a case.
     */
    async addParty(caseId, party) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return false;
        const managedParty = {
            ...party,
            partyId: (0, uuid_1.v4)(),
            addedAt: new Date(),
        };
        targetCase.parties.push(party);
        targetCase.managedParties.push(managedParty);
        targetCase.updatedAt = new Date();
        return this.storage.saveCase(targetCase.caseId, targetCase);
    }
    /**
     * Add a fact to a case.
     */
    async addFact(caseId, fact) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return false;
        targetCase.facts.push(fact);
        targetCase.updatedAt = new Date();
        return this.storage.saveCase(targetCase.caseId, targetCase);
    }
    /**
     * Add a deadline to a case.
     */
    async addDeadline(caseId, deadline) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return false;
        const fullDeadline = {
            ...deadline,
            deadlineId: (0, uuid_1.v4)(),
            completed: false,
            createdAt: new Date(),
        };
        targetCase.deadlines.push(fullDeadline);
        targetCase.updatedAt = new Date();
        return this.storage.saveCase(targetCase.caseId, targetCase);
    }
    /**
     * Add a finding to a case.
     */
    async addFinding(caseId, finding) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return false;
        const fullFinding = {
            ...finding,
            findingId: (0, uuid_1.v4)(),
            timestamp: new Date(),
        };
        targetCase.managedFindings.push(fullFinding);
        targetCase.updatedAt = new Date();
        return this.storage.saveCase(targetCase.caseId, targetCase);
    }
    /**
     * Add a document reference to a case.
     */
    async addDocument(caseId, document) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return false;
        const fullDocument = {
            ...document,
            documentId: (0, uuid_1.v4)(),
            addedAt: new Date(),
        };
        targetCase.documents.push(fullDocument);
        targetCase.updatedAt = new Date();
        return this.storage.saveCase(targetCase.caseId, targetCase);
    }
    /**
     * Record an agent execution.
     */
    async recordAgentExecution(caseId, execution) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return false;
        const fullExecution = {
            ...execution,
            executionId: (0, uuid_1.v4)(),
            timestamp: new Date(),
        };
        targetCase.agentExecutions.push(fullExecution);
        targetCase.agentHistory.push(execution.agentId);
        targetCase.updatedAt = new Date();
        return this.storage.saveCase(targetCase.caseId, targetCase);
    }
    /**
     * Generate a case summary.
     */
    async generateSummary(caseId) {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return null;
        const now = new Date();
        const upcomingDeadlines = targetCase.deadlines
            .filter((d) => !d.completed && d.dueDate > now)
            .sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime())
            .slice(0, 5);
        const recentExecutions = [...targetCase.agentExecutions]
            .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
            .slice(0, 5);
        const openIssuesCount = targetCase.managedLegalIssues.filter((i) => i.status === "open").length;
        return {
            caseId: targetCase.caseId,
            title: targetCase.title,
            status: targetCase.status,
            caseType: targetCase.caseType,
            partiesCount: targetCase.parties.length,
            factsCount: targetCase.facts.length,
            findingsCount: targetCase.managedFindings.length,
            openIssuesCount,
            upcomingDeadlines,
            recentAgentExecutions: recentExecutions,
            createdAt: targetCase.createdAt,
            updatedAt: targetCase.updatedAt,
        };
    }
    /**
     * Export case data.
     */
    async exportCase(caseId, format = "json") {
        const targetCase = await this.getTargetCase(caseId);
        if (!targetCase)
            return null;
        if (format === "json") {
            return JSON.stringify(targetCase, null, 2);
        }
        // Markdown export
        return this.exportAsMarkdown(targetCase);
    }
    /**
     * Export case as Markdown.
     */
    exportAsMarkdown(caseData) {
        const lines = [];
        lines.push(`# Case: ${caseData.title}`);
        lines.push("");
        lines.push(`**Case ID:** ${caseData.caseId}`);
        lines.push(`**Status:** ${caseData.status}`);
        lines.push(`**Type:** ${caseData.caseType}`);
        lines.push(`**Created:** ${caseData.createdAt.toISOString()}`);
        lines.push(`**Updated:** ${caseData.updatedAt.toISOString()}`);
        lines.push("");
        // Jurisdiction
        lines.push("## Jurisdiction");
        lines.push(`- **Federal:** ${caseData.jurisdiction.federal ? "Yes" : "No"}`);
        if (caseData.jurisdiction.cantons.length > 0) {
            lines.push(`- **Cantons:** ${caseData.jurisdiction.cantons.join(", ")}`);
        }
        lines.push(`- **Languages:** ${caseData.jurisdiction.languages.join(", ")}`);
        lines.push("");
        // Parties
        if (caseData.parties.length > 0) {
            lines.push("## Parties");
            for (const party of caseData.parties) {
                lines.push(`- **${party.name}** (${party.role})`);
                if (party.contact) {
                    lines.push(`  - Contact: ${party.contact}`);
                }
            }
            lines.push("");
        }
        // Facts
        if (caseData.facts.length > 0) {
            lines.push("## Facts");
            for (const fact of caseData.facts) {
                lines.push(`- ${fact}`);
            }
            lines.push("");
        }
        // Deadlines
        if (caseData.deadlines.length > 0) {
            lines.push("## Deadlines");
            for (const deadline of caseData.deadlines) {
                const status = deadline.completed ? "[x]" : "[ ]";
                lines.push(`- ${status} **${deadline.name}** - ${deadline.dueDate.toISOString().split("T")[0]}`);
                if (deadline.description) {
                    lines.push(`  - ${deadline.description}`);
                }
            }
            lines.push("");
        }
        // Findings
        if (caseData.managedFindings.length > 0) {
            lines.push("## Findings");
            for (const finding of caseData.managedFindings) {
                lines.push(`### ${finding.category}`);
                lines.push(finding.content);
                lines.push(`- **Source:** ${finding.source}`);
                lines.push(`- **Confidence:** ${(finding.confidence * 100).toFixed(0)}%`);
                if (finding.citations.length > 0) {
                    lines.push(`- **Citations:** ${finding.citations.join(", ")}`);
                }
                lines.push("");
            }
        }
        // Agent Executions
        if (caseData.agentExecutions.length > 0) {
            lines.push("## Agent Activity");
            for (const exec of caseData.agentExecutions) {
                lines.push(`- **${exec.agentId}** (${exec.timestamp.toISOString().split("T")[0]}): ${exec.task}`);
                lines.push(`  - Outcome: ${exec.outcome}`);
                if (exec.summary) {
                    lines.push(`  - Summary: ${exec.summary}`);
                }
            }
            lines.push("");
        }
        // Documents
        if (caseData.documents.length > 0) {
            lines.push("## Documents");
            for (const doc of caseData.documents) {
                lines.push(`- **${doc.name}** (${doc.documentType})`);
                lines.push(`  - Path: ${doc.path}`);
            }
            lines.push("");
        }
        lines.push("---");
        lines.push(`*Exported on ${new Date().toISOString()} by BetterCallClaude*`);
        return lines.join("\n");
    }
    /**
     * Get the target case (specified or current).
     */
    async getTargetCase(caseId) {
        if (caseId) {
            return this.storage.loadCase(caseId);
        }
        return this._currentCase;
    }
    /**
     * Convert ManagedCaseContext to simple CaseContext for agents.
     */
    toAgentContext(managed) {
        return {
            caseId: managed.caseId,
            title: managed.title,
            caseType: managed.caseType,
            jurisdiction: managed.jurisdiction,
            parties: managed.parties,
            facts: managed.facts,
            legalIssues: managed.legalIssues,
            agentHistory: managed.agentHistory,
            findings: managed.findings,
            createdAt: managed.createdAt,
        };
    }
}
exports.CaseManager = CaseManager;
// =============================================================================
// Exports
// =============================================================================
exports.default = CaseManager;
//# sourceMappingURL=case-manager.js.map