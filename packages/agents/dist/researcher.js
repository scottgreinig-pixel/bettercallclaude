"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.MockMCPClient = exports.ResearcherAgent = exports.ResearchDepth = exports.LegalDomain = void 0;
const base_1 = require("./base");
// =============================================================================
// Research-Specific Enums and Types
// =============================================================================
/**
 * Swiss legal domains for classification.
 */
var LegalDomain;
(function (LegalDomain) {
    LegalDomain["CONTRACT"] = "contract";
    LegalDomain["TORT"] = "tort";
    LegalDomain["PROPERTY"] = "property";
    LegalDomain["FAMILY"] = "family";
    LegalDomain["SUCCESSION"] = "succession";
    LegalDomain["CORPORATE"] = "corporate";
    LegalDomain["EMPLOYMENT"] = "employment";
    LegalDomain["CRIMINAL"] = "criminal";
    LegalDomain["ADMINISTRATIVE"] = "administrative";
    LegalDomain["PROCEDURAL"] = "procedural";
    LegalDomain["DEBT_COLLECTION"] = "debt_collection";
    LegalDomain["INTELLECTUAL_PROPERTY"] = "ip";
    LegalDomain["OTHER"] = "other";
})(LegalDomain || (exports.LegalDomain = LegalDomain = {}));
/**
 * Research depth levels.
 */
var ResearchDepth;
(function (ResearchDepth) {
    ResearchDepth["QUICK"] = "quick";
    ResearchDepth["STANDARD"] = "standard";
    ResearchDepth["DEEP"] = "deep";
})(ResearchDepth || (exports.ResearchDepth = ResearchDepth = {}));
/**
 * Default mock MCP client for development.
 */
class MockMCPClient {
    async call(server, method, params) {
        if (server === "bge-search" && method === "search") {
            return {
                results: [
                    {
                        id: "BGE-142-III-234",
                        title: "Werkvertrag; Mängelhaftung",
                        citation: "BGE 142 III 234",
                        date: "2016-05-15",
                        court: "Bundesgericht",
                        summary: "Grundsatzentscheid zur Mängelhaftung im Werkvertrag...",
                        relevance_score: 0.95,
                        full_text_url: "https://bger.ch/ext/142-III-234",
                    },
                ],
                total: 1,
            };
        }
        else if (server === "cantonal-courts" && method === "search") {
            return { results: [], total: 0 };
        }
        else if (server === "legal-citations" && method === "verify") {
            return {
                verified: true,
                formatted: params.citation || "",
                is_current: true,
                issues: [],
            };
        }
        return { results: [], total: 0 };
    }
}
exports.MockMCPClient = MockMCPClient;
// =============================================================================
// Researcher Agent
// =============================================================================
/**
 * Legal research agent for Swiss law.
 *
 * Performs deep, multi-source research with citation verification.
 * Implements the workflow defined in AGENT_RESEARCHER_SPEC.md.
 */
class ResearcherAgent extends base_1.AgentBase {
    // Swiss statute mappings
    static SWISS_STATUTES = {
        OR: "Obligationenrecht",
        ZGB: "Zivilgesetzbuch",
        StGB: "Strafgesetzbuch",
        ZPO: "Zivilprozessordnung",
        StPO: "Strafprozessordnung",
        SchKG: "Schuldbetreibungs- und Konkursgesetz",
        VwVG: "Verwaltungsverfahrensgesetz",
        BGG: "Bundesgerichtsgesetz",
    };
    static SWISS_CANTONS = [
        "ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR",
        "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG",
        "TI", "VD", "VS", "NE", "GE", "JU",
    ];
    static DOMAIN_KEYWORDS = {
        [LegalDomain.CONTRACT]: [
            "Vertrag", "Werkvertrag", "Kaufvertrag", "Miete", "Pacht",
            "Mängel", "Gewährleistung", "Verzug", "Schadenersatz", "OR",
        ],
        [LegalDomain.TORT]: [
            "Haftung", "Haftpflicht", "Schaden", "Kausalität", "Verschulden",
            "Gefährdungshaftung", "unerlaubte Handlung",
        ],
        [LegalDomain.EMPLOYMENT]: [
            "Arbeit", "Kündigung", "Arbeitsvertrag", "Lohn", "Überstunden",
            "Ferienanspruch", "Arbeitszeugnis",
        ],
        [LegalDomain.CORPORATE]: [
            "AG", "GmbH", "Aktie", "Generalversammlung", "Verwaltungsrat",
            "Gesellschaft", "Kapital",
        ],
        [LegalDomain.CRIMINAL]: [
            "Straf", "Betrug", "Diebstahl", "Körperverletzung", "StGB",
        ],
        [LegalDomain.DEBT_COLLECTION]: [
            "Betreibung", "Konkurs", "Pfändung", "Rechtsvorschlag", "SchKG",
        ],
        [LegalDomain.PROPERTY]: [],
        [LegalDomain.FAMILY]: [],
        [LegalDomain.SUCCESSION]: [],
        [LegalDomain.ADMINISTRATIVE]: [],
        [LegalDomain.PROCEDURAL]: [],
        [LegalDomain.INTELLECTUAL_PROPERTY]: [],
        [LegalDomain.OTHER]: [],
    };
    mcpClient;
    constructor(config = {}) {
        super(config);
        this.mcpClient = config.mcpClient ?? new MockMCPClient();
    }
    get agentId() {
        return "researcher";
    }
    get agentVersion() {
        return "1.0.0";
    }
    /**
     * Execute legal research workflow.
     */
    async execute(task, options) {
        this.startTime = new Date();
        this.resetState();
        const depth = this.parseDepth(options?.depth);
        const maxSources = options?.maxSources ?? 50;
        this.updateState("depth", depth);
        this.updateState("maxSources", maxSources);
        this.createCheckpoint("auto", "Research started");
        try {
            // Step 1: UNDERSTAND
            const params = await this.understand(task);
            this.createCheckpoint("auto", "Parameters extracted");
            // Step 2: PLAN
            const strategy = await this.plan(params, depth, maxSources);
            if (this.autonomyMode === base_1.AutonomyMode.CAUTIOUS) {
                await this.confirmStrategy(strategy);
            }
            else if (this.autonomyMode === base_1.AutonomyMode.BALANCED) {
                await this.showStrategySummary(strategy);
            }
            // Step 3: SEARCH
            const results = await this.search(strategy);
            this.createCheckpoint("auto", `Search completed: ${results.results.length} results`);
            // Step 4: VERIFY
            const verification = await this.verify(results);
            if (this.autonomyMode === base_1.AutonomyMode.CAUTIOUS ||
                this.autonomyMode === base_1.AutonomyMode.BALANCED) {
                await this.reportVerification(verification);
            }
            // Step 5: SYNTHESIZE
            const synthesis = await this.synthesize(results, verification, params);
            this.createCheckpoint("auto", "Synthesis completed");
            // Step 6: DELIVER
            const memo = await this.deliver(synthesis, params, results, verification);
            return this.createSuccessResult(memo);
        }
        catch (error) {
            this.handleError(error);
            return this.createFailureResult(error);
        }
    }
    parseDepth(depth) {
        if (!depth)
            return ResearchDepth.STANDARD;
        if (Object.values(ResearchDepth).includes(depth)) {
            return depth;
        }
        return ResearchDepth.STANDARD;
    }
    // ---------------------------------------------------------------------------
    // Step 1: UNDERSTAND
    // ---------------------------------------------------------------------------
    async understand(question) {
        const start = Date.now();
        const domains = this.detectDomains(question);
        const keyTerms = this.extractKeyTerms(question);
        const statuteRefs = this.extractStatuteReferences(question);
        const [federal, cantons] = this.detectJurisdiction(question);
        const languages = this.detectLanguages(question);
        const concepts = this.extractConcepts(question, domains);
        const params = {
            originalQuestion: question,
            legalDomains: domains,
            keyTerms,
            concepts,
            jurisdictionFederal: federal,
            jurisdictionCantons: cantons,
            languages,
            statuteReferences: statuteRefs,
        };
        const durationMs = Date.now() - start;
        this.recordAction(base_1.ActionType.ANALYZE, "Parsed research question", { question }, {
            domains: domains.map((d) => d),
            keyTerms,
            cantons,
        }, durationMs);
        this.updateState("parameters", params);
        return params;
    }
    detectDomains(question) {
        const questionLower = question.toLowerCase();
        const detected = [];
        for (const [domain, keywords] of Object.entries(ResearcherAgent.DOMAIN_KEYWORDS)) {
            for (const keyword of keywords) {
                if (questionLower.includes(keyword.toLowerCase())) {
                    const domainEnum = domain;
                    if (!detected.includes(domainEnum)) {
                        detected.push(domainEnum);
                    }
                    break;
                }
            }
        }
        if (detected.length === 0) {
            detected.push(LegalDomain.OTHER);
        }
        return detected;
    }
    extractKeyTerms(question) {
        const stopwords = new Set([
            "der", "die", "das", "und", "oder", "ist", "sind", "was",
            "wie", "wer", "welche", "welcher", "nach", "bei", "für",
            "the", "and", "or", "is", "are", "what", "how", "which",
        ]);
        const words = question.match(/\b\w+\b/g) || [];
        const terms = [];
        for (const word of words) {
            if (word.length > 3 && !stopwords.has(word.toLowerCase())) {
                if (word[0] === word[0].toUpperCase() || word === word.toUpperCase()) {
                    terms.push(word);
                }
            }
        }
        // Extract quoted phrases
        const quoted = question.match(/"([^"]+)"/g) || [];
        terms.push(...quoted.map((q) => q.replace(/"/g, "")));
        return [...new Set(terms)].slice(0, 20);
    }
    extractStatuteReferences(question) {
        const patterns = [
            /Art\.?\s*\d+(?:\s*(?:Abs|lit|Ziff)\.?\s*\d+)*\s*(?:OR|ZGB|StGB|ZPO|StPO|SchKG|BGG)/gi,
            /§\s*\d+\s*[A-Za-z]+/g,
        ];
        const refs = [];
        for (const pattern of patterns) {
            const matches = question.match(pattern) || [];
            refs.push(...matches);
        }
        return [...new Set(refs)];
    }
    detectJurisdiction(question) {
        const questionUpper = question.toUpperCase();
        const cantons = [];
        for (const canton of ResearcherAgent.SWISS_CANTONS) {
            if (questionUpper.includes(canton) ||
                questionUpper.includes(`KANTON ${canton}`)) {
                cantons.push(canton);
            }
        }
        const cantonalKeywords = [
            "kantonal", "cantonal", "Obergericht", "Handelsgericht",
        ];
        const hasCantonal = cantonalKeywords.some((kw) => question.toLowerCase().includes(kw.toLowerCase()));
        const federalKeywords = ["BGE", "Bundesgericht", "federal", "eidgenössisch"];
        const hasFederal = federalKeywords.some((kw) => question.toLowerCase().includes(kw.toLowerCase()));
        const federal = hasFederal || (!hasCantonal && cantons.length === 0);
        return [federal, cantons];
    }
    detectLanguages(question) {
        const indicators = {
            DE: ["Vertrag", "Recht", "Gesetz", "Urteil"],
            FR: ["contrat", "droit", "loi", "arrêt"],
            IT: ["contratto", "diritto", "legge", "sentenza"],
            EN: ["contract", "law", "judgment", "ruling"],
        };
        const languages = [];
        for (const [lang, words] of Object.entries(indicators)) {
            if (words.some((word) => question.includes(word))) {
                languages.push(lang);
            }
        }
        return languages.length > 0 ? languages : ["DE"];
    }
    extractConcepts(question, domains) {
        const conceptMap = {
            [LegalDomain.CONTRACT]: [
                "Vertragsabschluss", "Vertragserfüllung", "Vertragsverletzung",
                "Leistungsstörung", "Mängelhaftung", "Gewährleistung",
            ],
            [LegalDomain.TORT]: [
                "Kausalzusammenhang", "Widerrechtlichkeit", "Verschulden",
                "Schaden", "Haftungsvoraussetzungen",
            ],
            [LegalDomain.EMPLOYMENT]: [
                "Arbeitspflicht", "Fürsorgepflicht", "Treuepflicht",
                "Kündigungsschutz", "Lohnanspruch",
            ],
        };
        const concepts = [];
        for (const domain of domains) {
            const domainConcepts = conceptMap[domain] || [];
            for (const concept of domainConcepts) {
                if (question.toLowerCase().includes(concept.toLowerCase())) {
                    concepts.push(concept);
                }
            }
        }
        return [...new Set(concepts)];
    }
    // ---------------------------------------------------------------------------
    // Step 2: PLAN
    // ---------------------------------------------------------------------------
    async plan(params, depth, maxSources) {
        const start = Date.now();
        const sources = this.configureSources(params);
        const queries = this.generateQueries(params, sources);
        const parallelConfig = {
            [ResearchDepth.QUICK]: 3,
            [ResearchDepth.STANDARD]: 5,
            [ResearchDepth.DEEP]: 8,
        };
        const strategy = {
            sources,
            queries,
            relevanceThreshold: 0.5,
            maxTotalResults: maxSources,
            parallelLimit: parallelConfig[depth],
        };
        const durationMs = Date.now() - start;
        this.recordAction(base_1.ActionType.ANALYZE, "Created search strategy", { depth, maxSources }, {
            sourcesCount: sources.length,
            queriesCount: queries.length,
        }, durationMs);
        this.updateState("strategy", strategy);
        return strategy;
    }
    configureSources(params) {
        const sources = [];
        if (params.jurisdictionFederal) {
            sources.push({
                name: "BGE",
                priority: 1,
                expectedVolume: 30,
                mcpServer: "bge-search",
                searchMethod: "search",
            });
        }
        for (const canton of params.jurisdictionCantons) {
            sources.push({
                name: `Cantonal-${canton}`,
                priority: 2,
                expectedVolume: 20,
                mcpServer: "cantonal-courts",
                searchMethod: "search",
            });
        }
        sources.push({
            name: "Entscheidsuche",
            priority: 3,
            expectedVolume: 50,
            mcpServer: "entscheidsuche",
            searchMethod: "search",
        });
        return sources;
    }
    generateQueries(params, sources) {
        const queries = [];
        const baseQuery = params.keyTerms.slice(0, 5).join(" ");
        const statuteQuery = params.statuteReferences.join(" OR ");
        for (const source of sources) {
            let queryText = baseQuery;
            if (statuteQuery) {
                queryText = `(${baseQuery}) AND (${statuteQuery})`;
            }
            const filters = {};
            if (params.timeRangeFrom) {
                filters.date_from = params.timeRangeFrom.toISOString();
            }
            if (params.timeRangeTo) {
                filters.date_to = params.timeRangeTo.toISOString();
            }
            for (const lang of params.languages) {
                queries.push({
                    source: source.name,
                    query: queryText,
                    filters,
                    language: lang,
                    maxResults: source.expectedVolume,
                });
            }
        }
        return queries;
    }
    async confirmStrategy(strategy) {
        const summary = `Search strategy:\n` +
            `- ${strategy.sources.length} sources\n` +
            `- ${strategy.queries.length} queries\n` +
            `- Max ${strategy.maxTotalResults} results\n` +
            `Proceed?`;
        await this.requestUserConfirmation(summary);
    }
    async showStrategySummary(_strategy) {
        // In real implementation, would display to user
    }
    // ---------------------------------------------------------------------------
    // Step 3: SEARCH
    // ---------------------------------------------------------------------------
    async search(strategy) {
        const start = Date.now();
        const allResults = [];
        const bySource = {};
        // Execute queries in parallel batches
        for (let i = 0; i < strategy.queries.length; i += strategy.parallelLimit) {
            const batch = strategy.queries.slice(i, i + strategy.parallelLimit);
            const batchResults = await Promise.allSettled(batch.map((q) => this.executeQuery(q)));
            for (let j = 0; j < batch.length; j++) {
                const query = batch[j];
                const result = batchResults[j];
                if (result.status === "rejected") {
                    this.handleSearchError(result.reason, query.source);
                    continue;
                }
                const sourceResults = this.parseResults(result.value, query.source);
                allResults.push(...sourceResults);
                if (!bySource[query.source]) {
                    bySource[query.source] = [];
                }
                bySource[query.source].push(...sourceResults);
                this.recordSourceAccess(query.source);
            }
        }
        // Deduplicate and sort
        let deduplicated = this.deduplicateResults(allResults);
        deduplicated.sort((a, b) => b.relevanceScore - a.relevanceScore);
        deduplicated = deduplicated.slice(0, strategy.maxTotalResults);
        const durationMs = Date.now() - start;
        this.recordAction(base_1.ActionType.SEARCH, "Executed parallel searches", { queries: strategy.queries.length }, {
            totalFound: allResults.length,
            deduplicated: deduplicated.length,
        }, durationMs);
        return {
            results: deduplicated,
            bySource,
            totalFound: allResults.length,
            deduplicatedCount: deduplicated.length,
            processingTimeMs: durationMs,
        };
    }
    async executeQuery(query) {
        const mcpServer = this.getMcpServer(query.source);
        return await this.mcpClient.call(mcpServer, "search", {
            query: query.query,
            filters: query.filters,
            language: query.language,
            limit: query.maxResults,
        });
    }
    getMcpServer(sourceName) {
        if (sourceName === "BGE") {
            return "bge-search";
        }
        else if (sourceName.startsWith("Cantonal-")) {
            return "cantonal-courts";
        }
        return "entscheidsuche";
    }
    parseResults(response, source) {
        const results = [];
        const items = response.results || [];
        for (const item of items) {
            try {
                let date;
                if (item.date) {
                    date = new Date(String(item.date).replace("Z", "+00:00"));
                }
                results.push({
                    id: String(item.id || ""),
                    title: String(item.title || ""),
                    citation: String(item.citation || ""),
                    date,
                    court: String(item.court || ""),
                    summary: String(item.summary || ""),
                    relevanceScore: Number(item.relevance_score || 0.5),
                    source,
                    fullTextUrl: item.full_text_url
                        ? String(item.full_text_url)
                        : undefined,
                    language: String(item.language || "DE"),
                });
            }
            catch {
                // Skip malformed results
            }
        }
        return results;
    }
    deduplicateResults(results) {
        const seenCitations = new Set();
        const unique = [];
        for (const result of results) {
            const citationKey = result.citation.toLowerCase().trim();
            if (citationKey && !seenCitations.has(citationKey)) {
                seenCitations.add(citationKey);
                unique.push(result);
            }
        }
        return unique;
    }
    handleSearchError(error, source) {
        console.error(`Search error for ${source}:`, error);
    }
    // ---------------------------------------------------------------------------
    // Step 4: VERIFY
    // ---------------------------------------------------------------------------
    async verify(results) {
        const start = Date.now();
        const verified = [];
        const outdated = [];
        const errors = [];
        const citations = [
            ...new Set(results.results.map((r) => r.citation).filter(Boolean)),
        ];
        for (const citation of citations) {
            try {
                const response = await this.mcpClient.call("legal-citations", "verify", {
                    citation,
                });
                const verifiedCitation = {
                    citation,
                    isValid: Boolean(response.verified),
                    isCurrent: Boolean(response.is_current ?? true),
                    formatted: String(response.formatted || citation),
                    court: String(response.court || ""),
                    date: undefined,
                    issues: response.issues || [],
                };
                if (verifiedCitation.isCurrent) {
                    verified.push(verifiedCitation);
                }
                else {
                    outdated.push(verifiedCitation);
                }
            }
            catch (e) {
                errors.push({
                    citation,
                    error: String(e),
                });
            }
        }
        const total = verified.length + outdated.length + errors.length;
        const accuracy = total > 0 ? verified.length / total : 1.0;
        const durationMs = Date.now() - start;
        this.recordAction(base_1.ActionType.ANALYZE, "Verified citations", { citationsCount: citations.length }, {
            verified: verified.length,
            outdated: outdated.length,
            errors: errors.length,
            accuracy,
        }, durationMs);
        return {
            verified,
            outdated,
            errors,
            overallAccuracy: accuracy,
        };
    }
    async reportVerification(report) {
        if (report.outdated.length > 0 || report.errors.length > 0) {
            const message = `Citation verification complete:\n` +
                `- ${report.verified.length} verified\n` +
                `- ${report.outdated.length} outdated\n` +
                `- ${report.errors.length} errors\n` +
                `Continue with synthesis?`;
            await this.requestUserConfirmation(message);
        }
    }
    // ---------------------------------------------------------------------------
    // Step 5: SYNTHESIZE
    // ---------------------------------------------------------------------------
    async synthesize(results, verification, params) {
        const start = Date.now();
        const grouped = this.groupByIssue(results.results, params);
        const findings = [];
        for (const [issue, issueResults] of Object.entries(grouped)) {
            const finding = this.generateFinding(issue, issueResults, verification);
            findings.push(finding);
        }
        const precedentChain = this.buildPrecedentChain(results.results);
        const conflicts = this.identifyConflicts(findings);
        const gaps = this.identifyGaps(params, findings);
        const recommendations = this.generateRecommendations(findings, gaps);
        const durationMs = Date.now() - start;
        this.recordAction(base_1.ActionType.ANALYZE, "Synthesized research findings", { resultsCount: results.results.length }, {
            findings: findings.length,
            conflicts: conflicts.length,
            gaps: gaps.length,
        }, durationMs);
        return {
            keyFindings: findings,
            precedentChain,
            conflicts,
            gaps,
            recommendations,
        };
    }
    groupByIssue(results, params) {
        const grouped = {};
        for (const result of results) {
            for (const domain of params.legalDomains) {
                const issue = domain;
                if (!grouped[issue]) {
                    grouped[issue] = [];
                }
                grouped[issue].push(result);
            }
        }
        return grouped;
    }
    generateFinding(issue, results, verification) {
        const resultCitations = results.map((r) => r.citation);
        const verifiedCitations = verification.verified
            .filter((v) => resultCitations.includes(v.citation))
            .map((v) => v.formatted);
        const confidence = Math.min(verifiedCitations.length / 5, 1.0);
        let conclusion;
        if (results.length > 0) {
            conclusion = `Based on ${results.length} precedents, the legal position on ${issue} is established.`;
        }
        else {
            conclusion = `No clear precedent found for ${issue}.`;
        }
        return {
            issue,
            conclusion,
            supportingCitations: verifiedCitations.slice(0, 5),
            confidence,
            conflicts: [],
        };
    }
    buildPrecedentChain(results) {
        const dated = results.filter((r) => r.date);
        dated.sort((a, b) => (a.date?.getTime() || 0) - (b.date?.getTime() || 0));
        return dated.slice(0, 10).map((r) => r.citation);
    }
    identifyConflicts(_findings) {
        // Simplified - would use more sophisticated analysis
        return [];
    }
    identifyGaps(params, findings) {
        const gaps = [];
        const coveredIssues = new Set(findings.map((f) => f.issue));
        for (const domain of params.legalDomains) {
            if (!coveredIssues.has(domain)) {
                gaps.push(`No findings for ${domain}`);
            }
        }
        const lowConfidence = findings.filter((f) => f.confidence < 0.5);
        for (const finding of lowConfidence) {
            gaps.push(`Low confidence for ${finding.issue}`);
        }
        return gaps;
    }
    generateRecommendations(findings, gaps) {
        const recommendations = [];
        if (gaps.length > 0) {
            recommendations.push("Consider additional research to address gaps");
        }
        const lowConfidence = findings.filter((f) => f.confidence < 0.7);
        if (lowConfidence.length > 0) {
            recommendations.push("Consult doctrine for low-confidence findings");
        }
        return recommendations;
    }
    // ---------------------------------------------------------------------------
    // Step 6: DELIVER
    // ---------------------------------------------------------------------------
    async deliver(synthesis, params, results, verification) {
        const start = Date.now();
        const executiveSummary = this.generateExecutiveSummary(synthesis, params);
        const methodology = this.generateMethodology(params, results);
        const limitations = this.compileLimitations(results, verification);
        const nextSteps = [...synthesis.recommendations];
        if (synthesis.gaps.length > 0) {
            nextSteps.push("Address identified research gaps");
        }
        const metadata = {
            researchDate: new Date().toISOString(),
            question: params.originalQuestion,
            sourcesSearched: Object.keys(results.bySource).length,
            totalResults: results.totalFound,
            verifiedCitations: verification.verified.length,
            processingTimeMs: results.processingTimeMs,
            autonomyMode: this.autonomyMode,
        };
        const durationMs = Date.now() - start;
        this.recordAction(base_1.ActionType.GENERATE, "Generated research memo", {}, { sections: 6 }, durationMs);
        const memo = {
            title: `Research Memo: ${params.originalQuestion.slice(0, 50)}...`,
            executiveSummary,
            methodology,
            findings: synthesis.keyFindings,
            citations: verification.verified,
            limitations,
            nextSteps,
            metadata,
        };
        this.recordDocumentWrite("research_memo");
        return memo;
    }
    generateExecutiveSummary(synthesis, params) {
        const findingsSummary = [];
        for (const finding of synthesis.keyFindings) {
            if (finding.confidence >= 0.7) {
                findingsSummary.push(finding.conclusion);
            }
        }
        if (findingsSummary.length > 0) {
            return findingsSummary.slice(0, 3).join(" ");
        }
        return `Research completed for: ${params.originalQuestion}. See detailed findings below.`;
    }
    generateMethodology(params, results) {
        const sources = Object.keys(results.bySource);
        return (`This research analyzed ${results.totalFound} sources from ${sources.length} databases ` +
            `(${sources.join(", ")}). Results were deduplicated and verified for currency. ` +
            `Languages: ${params.languages.join(", ")}.`);
    }
    compileLimitations(results, verification) {
        const limitations = [];
        if (verification.outdated.length > 0) {
            limitations.push(`${verification.outdated.length} citations may be outdated`);
        }
        if (verification.errors.length > 0) {
            limitations.push(`${verification.errors.length} citations could not be verified`);
        }
        return limitations;
    }
    // ---------------------------------------------------------------------------
    // Result Creation
    // ---------------------------------------------------------------------------
    createSuccessResult(memo) {
        const executionTime = Date.now() - (this.startTime?.getTime() ?? Date.now());
        const auditLog = this.createAuditLog(base_1.AgentOutcome.SUCCESS, ["research_memo"]);
        return {
            success: true,
            outcome: base_1.AgentOutcome.SUCCESS,
            deliverable: memo,
            partialResults: undefined,
            errorMessage: undefined,
            auditLog,
            executionTimeMs: executionTime,
        };
    }
    createFailureResult(error) {
        const executionTime = Date.now() - (this.startTime?.getTime() ?? Date.now());
        const params = this.getState("parameters");
        const partial = params ? this.createPartialResult(params) : undefined;
        const auditLog = this.createAuditLog(base_1.AgentOutcome.FAILED, []);
        return {
            success: false,
            outcome: base_1.AgentOutcome.FAILED,
            deliverable: undefined,
            // Cast partial results - contains recovery metadata, not a full ResearchMemo
            partialResults: partial,
            errorMessage: error.message,
            auditLog,
            executionTimeMs: executionTime,
        };
    }
}
exports.ResearcherAgent = ResearcherAgent;
//# sourceMappingURL=researcher.js.map