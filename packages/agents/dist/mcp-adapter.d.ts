/**
 * MCP Adapter for Legal Research Agents
 *
 * Provides real MCP client implementation that connects to MCP servers
 * (entscheidsuche, legal-citations) over stdio transport.
 *
 * This adapter implements the MCPClient interface expected by ResearcherAgent
 * and routes calls to the appropriate MCP server.
 */
import type { MCPClient } from "./researcher";
/**
 * Configuration for an MCP server connection
 */
export interface MCPServerConfig {
    name: string;
    command: string;
    args: string[];
    env?: Record<string, string>;
}
/**
 * Configuration for the MCP adapter
 */
export interface MCPAdapterConfig {
    /** Path to entscheidsuche MCP server */
    entscheidsuchePath?: string;
    /** Path to legal-citations MCP server */
    legalCitationsPath?: string;
    /** Additional environment variables */
    env?: Record<string, string>;
    /** Connection timeout in milliseconds */
    timeout?: number;
}
/**
 * Real MCP client adapter that connects to actual MCP servers.
 *
 * Implements the MCPClient interface expected by ResearcherAgent and
 * manages connections to entscheidsuche and legal-citations MCP servers.
 *
 * @example
 * ```typescript
 * const adapter = new MCPAdapter({
 *   entscheidsuchePath: './mcp-servers/entscheidsuche/dist/index.js',
 *   legalCitationsPath: './mcp-servers/legal-citations/dist/index.js',
 * });
 *
 * await adapter.connect();
 *
 * const result = await adapter.call('entscheidsuche', 'search', {
 *   query: 'Werkvertrag Mängel',
 *   limit: 10,
 * });
 *
 * await adapter.disconnect();
 * ```
 */
export declare class MCPAdapter implements MCPClient {
    private config;
    private connections;
    private serverConfigs;
    constructor(config?: MCPAdapterConfig);
    /**
     * Initialize server configurations based on provided paths
     */
    private initializeServerConfigs;
    /**
     * Connect to all configured MCP servers
     */
    connect(): Promise<void>;
    /**
     * Connect to a specific MCP server
     */
    private connectToServer;
    /**
     * Disconnect from all MCP servers
     */
    disconnect(): Promise<void>;
    /**
     * Call an MCP server method.
     *
     * This is the main interface method that ResearcherAgent uses.
     * It translates server names and method names to actual MCP tool calls.
     *
     * @param server - Logical server name (e.g., 'bge-search', 'legal-citations')
     * @param method - Method name (e.g., 'search', 'verify')
     * @param params - Parameters for the method call
     * @returns Result from the MCP server
     */
    call(server: string, method: string, params: Record<string, unknown>): Promise<Record<string, unknown>>;
    /**
     * Transform parameters for specific server/method combinations
     */
    private transformParams;
    /**
     * Parse MCP result to expected format
     */
    private parseResult;
    /**
     * Transform result to expected ResearcherAgent format
     */
    private transformResult;
    /**
     * Check if connected to a specific server
     */
    isConnected(server?: string): boolean;
    /**
     * List available servers
     */
    getAvailableServers(): string[];
}
/**
 * Create an MCP adapter with default configuration
 */
export declare function createMCPAdapter(config?: MCPAdapterConfig): MCPAdapter;
/**
 * Create and connect an MCP adapter
 */
export declare function createConnectedMCPAdapter(config?: MCPAdapterConfig): Promise<MCPAdapter>;
export type { MCPClient };
//# sourceMappingURL=mcp-adapter.d.ts.map