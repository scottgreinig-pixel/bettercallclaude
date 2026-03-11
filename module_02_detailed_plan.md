**Module 2: Mastering Legal Research with BetterCallClaude**

**Module Goal:** To empower legal professionals with the skills to conduct comprehensive and efficient legal research using BetterCallClaude. This module will cover everything from basic natural language queries to advanced precedent analysis, with a focus on the specific tools and agents available within the BetterCallClaude framework.

---

**Lesson 1: The `/legal:research` Command**

*   **Learning Objectives:**
    *   Conduct basic legal research using natural language queries.
    *   Apply advanced search techniques, including the use of keywords, jurisdictions, and date ranges.
    *   Effectively understand and interpret the search results provided by BetterCallClaude.

*   **Key Concepts:**
    *   The `/legal:research` command
    *   Natural language queries
    *   Advanced search operators (keywords, jurisdictions, date ranges)
    *   Search result interpretation
    *   Source evaluation and critical analysis

*   **Lesson Plan:**
    *   **(1) Introduction to the `/legal:research` Command (15 minutes):**
        *   **Presentation:** Introduce the `/legal:research` command as the primary tool for conducting legal research in BetterCallClaude. Explain its syntax and basic usage.
        *   **Demonstration:** Showcase a simple research query using natural language, such as `/legal:research "liability for defective products"`.

    *   **(2) Advanced Search Techniques (25 minutes):**
        *   **Presentation:**
            *   **Keywords:** Explain how to use specific keywords to narrow down search results.
            *   **Jurisdictions:** Demonstrate how to limit searches to specific jurisdictions (e.g., `/legal:research "rental law" --jurisdiction=ZH`).
            *   **Date Ranges:** Show how to filter results by date (e.g., `/legal:research "BGE 147 V 321" --date-from=2020-01-01`).
        *   **Activity: "Query Crafting":** Provide learners with a series of research scenarios and ask them to craft the appropriate advanced search queries.

    *   **(3) Understanding and Interpreting Search Results (15 minutes):**
        *   **Presentation:** Explain how BetterCallClaude presents search results, including snippets, source information, and relevance ranking.
        *   **Activity: "Result Analysis":** Give learners a set of search results and ask them to identify the most relevant documents and explain their reasoning.

---

**Lesson 2: Precedent & Statutory Analysis**

*   **Learning Objectives:**
    *   Use the `ResearcherAgent` for in-depth precedent analysis.
    *   Leverage the `entscheidsuche` and `bge-search` MCP servers for accessing primary sources.
    *   Verify and format legal citations using the `Citation Specialist` agent.

*   **Key Concepts:**
    *   `ResearcherAgent`
    *   Precedent analysis
    *   `entscheidsuche` and `bge-search` MCP servers
    *   `Citation Specialist` agent
    *   Citation verification and formatting

*   **Lesson Plan:**
    *   **(1) The `ResearcherAgent` for Precedent Analysis (20 minutes):**
        *   **Presentation:** Introduce the `ResearcherAgent` as a specialized agent for conducting in-depth precedent analysis. Explain how it can be used to identify relevant case law, track the development of legal doctrines, and assess the precedential value of court decisions.
        *   **Demonstration:** Showcase a use case where the `ResearcherAgent` is used to analyze a complex legal issue and generate a research memo.

    *   **(2) Accessing Primary Sources with MCP Servers (20 minutes):**
        *   **Presentation:** Explain the role of the `entscheidsuche` and `bge-search` MCP servers in providing direct access to Swiss federal and cantonal court decisions.
        *   **Activity: "Source Exploration":** Guide learners through the process of using the MCP servers to find and retrieve specific court decisions.

    *   **(3) The `Citation Specialist` Agent (15 minutes):**
        *   **Presentation:** Introduce the `Citation Specialist` agent as a tool for verifying and formatting legal citations. Explain its importance for ensuring accuracy and consistency in legal writing.
        *   **Demonstration:** Show how the `Citation Specialist` can be used to automatically format a list of citations according to a specific style guide.

---

**Lesson 3: Cantonal & Federal Law**

*   **Learning Objectives:**
    *   Navigate the complexities of Swiss federal and cantonal law.
    *   Use the `Cantonal Law` agent for jurisdiction-specific research.
    *   Apply best practices for multi-lingual legal research (DE, FR, IT).

*   **Key Concepts:**
    *   Swiss federal and cantonal law
    *   `Cantonal Law` agent
    *   Jurisdiction-specific research
    *   Multi-lingual legal research
    *   Language-specific legal terminology

*   **Lesson Plan:**
    *   **(1) Navigating Swiss Federal and Cantonal Law (15 minutes):**
        *   **Presentation:** Provide an overview of the Swiss legal system, explaining the relationship between federal and cantonal law.
        *   **Activity: "Jurisdiction Quiz":** Test learners' knowledge of Swiss cantons and their respective legal systems.

    *   **(2) The `Cantonal Law` Agent (20 minutes):**
        *   **Presentation:** Introduce the `Cantonal Law` agent as a specialized tool for conducting research on the specific laws of each of the 26 cantons.
        *   **Demonstration:** Showcase a use case where the `Cantonal Law` agent is used to research a legal issue in a specific canton, such as "Werkvertrag Mängelhaftung" in Zurich.

    *   **(3) Best Practices for Multi-lingual Legal Research (20 minutes):**
        *   **Presentation:** Discuss the challenges and opportunities of conducting legal research in a multi-lingual environment like Switzerland. Provide tips and best practices for working with legal documents in German, French, and Italian.
        *   **Activity: "Translation Challenge":** Give learners a legal phrase in one language and ask them to find the equivalent phrase in the other two official languages using BetterCallClaude's translation capabilities.
