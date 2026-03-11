"""
MCP Protocol Client for BetterCallClaude v2.0

This module implements the Model Context Protocol (MCP) client layer for
communication with MCP servers using stdio transport and JSON-RPC 2.0.

The MCP protocol enables:
- Server capability discovery
- Tool invocation with structured parameters
- Resource access and management
- Bidirectional communication via stdin/stdout
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types following JSON-RPC 2.0 spec"""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPCapability:
    """Represents a capability exposed by an MCP server"""

    name: str
    description: str
    parameters: dict[str, Any]
    returns: dict[str, Any] | None = None


@dataclass
class MCPServerInfo:
    """Information about an MCP server"""

    server_id: str
    name: str
    version: str
    capabilities: list[MCPCapability]
    protocol_version: str = "2024-11-05"


class MCPProtocolError(Exception):
    """Base exception for MCP protocol errors"""

    pass


class MCPConnectionError(MCPProtocolError):
    """Error establishing or maintaining MCP server connection"""

    pass


class MCPInvocationError(MCPProtocolError):
    """Error invoking MCP tool or capability"""

    pass


class MCPClient:
    """
    MCP Protocol Client for stdio-based server communication

    Implements JSON-RPC 2.0 protocol over stdin/stdout transport to
    communicate with MCP servers.

    Example:
        client = MCPClient(command=["node", "server.js"])
        await client.connect()

        # Discover capabilities
        info = await client.initialize()

        # Invoke tool
        result = await client.invoke_tool(
            "search_bge",
            {"query": "BGE 147 V 321"}
        )

        await client.disconnect()
    """

    def __init__(
        self,
        command: list[str],
        server_id: str,
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize MCP client

        Args:
            command: Command to start MCP server (e.g., ["node", "server.js"])
            server_id: Unique server identifier
            env: Optional environment variables for server process
            timeout: Request timeout in seconds
        """
        self.command = command
        self.server_id = server_id
        self.env = env or {}
        self.timeout = timeout

        self._process: subprocess.Popen | None = None
        self._server_info: MCPServerInfo | None = None
        self._request_id: int = 0
        self._connected: bool = False

    async def connect(self) -> None:
        """
        Start MCP server process and establish connection

        Raises:
            MCPConnectionError: If server fails to start
        """
        try:
            self._process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**self.env},
                text=True,
                bufsize=1,
            )

            # Wait briefly for process to start
            await asyncio.sleep(0.1)

            if self._process.poll() is not None:
                stderr = self._process.stderr.read() if self._process.stderr else ""
                raise MCPConnectionError(f"MCP server {self.server_id} failed to start: {stderr}")

            self._connected = True
            logger.info(f"Connected to MCP server: {self.server_id}")

        except Exception as e:
            raise MCPConnectionError(
                f"Failed to connect to MCP server {self.server_id}: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Terminate MCP server process and cleanup"""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

            self._connected = False
            logger.info(f"Disconnected from MCP server: {self.server_id}")

    async def initialize(self) -> MCPServerInfo:
        """
        Initialize connection and discover server capabilities

        Returns:
            MCPServerInfo with server metadata and capabilities

        Raises:
            MCPConnectionError: If not connected
            MCPProtocolError: If initialization fails
        """
        if not self._connected:
            raise MCPConnectionError("Client not connected to server")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "BetterCallClaude",
                    "version": "2.0.0",
                },
            },
        }

        response = await self._send_request(request)

        # Parse server info and capabilities
        result = response.get("result", {})
        server_info = result.get("serverInfo", {})
        capabilities_data = result.get("capabilities", {})

        capabilities = self._parse_capabilities(capabilities_data)

        self._server_info = MCPServerInfo(
            server_id=self.server_id,
            name=server_info.get("name", "Unknown"),
            version=server_info.get("version", "Unknown"),
            capabilities=capabilities,
            protocol_version=result.get("protocolVersion", "2024-11-05"),
        )

        logger.info(
            f"Initialized MCP server {self.server_id}: "
            f"{len(capabilities)} capabilities available"
        )

        return self._server_info

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Invoke a tool on the MCP server

        Args:
            tool_name: Name of tool to invoke
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPConnectionError: If not connected
            MCPInvocationError: If tool invocation fails
        """
        if not self._connected:
            raise MCPConnectionError("Client not connected to server")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        try:
            response = await self._send_request(request)

            if "error" in response:
                error = response["error"]
                raise MCPInvocationError(
                    f"Tool invocation failed: {error.get('message', 'Unknown error')}"
                )

            return cast(dict[str, Any], response.get("result", {}))

        except Exception as e:
            raise MCPInvocationError(f"Failed to invoke tool {tool_name}: {e}") from e

    async def _send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Send JSON-RPC request and wait for response

        Args:
            request: JSON-RPC request object

        Returns:
            JSON-RPC response object

        Raises:
            MCPProtocolError: If communication fails
        """
        if not self._process or not self._process.stdin:
            raise MCPProtocolError("No active server process")

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self._process.stdin.write(request_json)
            self._process.stdin.flush()

            # Read response with timeout
            if self._process.stdout is None:
                raise MCPProtocolError("Server stdout not available")

            response_line = await asyncio.wait_for(
                asyncio.to_thread(self._process.stdout.readline), timeout=self.timeout
            )

            if not response_line:
                raise MCPProtocolError("Server closed connection")

            response = cast(dict[str, Any], json.loads(response_line))

            # Validate response
            if response.get("id") != request.get("id"):
                raise MCPProtocolError(
                    f"Response ID mismatch: expected {request.get('id')}, "
                    f"got {response.get('id')}"
                )

            return response

        except TimeoutError as timeout_err:
            raise MCPProtocolError(f"Request timeout after {self.timeout}s") from timeout_err
        except json.JSONDecodeError as json_err:
            raise MCPProtocolError(f"Invalid JSON response: {json_err}") from json_err
        except Exception as e:
            raise MCPProtocolError(f"Communication error: {e}") from e

    def _parse_capabilities(self, capabilities_data: dict[str, Any]) -> list[MCPCapability]:
        """Parse capabilities from server initialization response"""
        capabilities = []

        # MCP servers expose capabilities through tools
        tools = capabilities_data.get("tools", {})
        if isinstance(tools, dict):
            tool_list = tools.get("tools", [])
            for tool in tool_list:
                capability = MCPCapability(
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    parameters=tool.get("inputSchema", {}),
                )
                capabilities.append(capability)

        return capabilities

    def _next_request_id(self) -> int:
        """Generate next request ID"""
        self._request_id += 1
        return self._request_id

    def get_server_info(self) -> MCPServerInfo | None:
        """Get cached server info (None if not initialized)"""
        return self._server_info

    def is_connected(self) -> bool:
        """Check if client is connected to server"""
        if not self._connected or not self._process:
            return False
        return self._process.poll() is None

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry"""
        await self.connect()
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.disconnect()
