"""
MCP Server Connection Manager for BetterCallClaude v2.0

This module provides connection pooling, health checks, and retry logic
for MCP server integrations.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .adapters import BGESearchAdapter, CantonalCourtsAdapter, EntscheidausucheAdapter

logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """MCP server connection status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class ServerHealth:
    """Health check result for MCP server"""

    server_id: str
    status: ServerStatus
    last_check: datetime
    response_time_ms: float | None
    error_message: str | None = None


@dataclass
class ServerConfig:
    """Configuration for MCP server connection"""

    server_id: str
    name: str
    description: str
    endpoint: str | None = None
    max_retries: int = 3
    timeout_seconds: int = 30
    health_check_interval: int = 60
    enabled: bool = True


class MCPConnectionManager:
    """
    Manages connections to MCP servers with pooling and health checks

    Features:
    - Connection pooling and reuse
    - Automatic retry with exponential backoff
    - Health monitoring and circuit breaking
    - Request timeout and rate limiting
    - Error handling and logging

    Example:
        manager = MCPConnectionManager()

        # Register server
        manager.register_server(
            server_id="bge_search",
            name="BGE Search MCP",
            endpoint="mcp://bge-search"
        )

        # Execute request
        result = await manager.execute(
            server_id="bge_search",
            method="search",
            params={"query": "BGE 147 V 321"}
        )

        # Check health
        health = await manager.check_health("bge_search")
    """

    def __init__(self, mcp_servers_path: Path | None = None) -> None:
        """
        Initialize MCP connection manager

        Args:
            mcp_servers_path: Path to MCP servers directory
                            (default: ./mcp-servers/)
        """
        if mcp_servers_path is None:
            mcp_servers_path = Path.cwd() / "mcp-servers"

        self.mcp_servers_path = Path(mcp_servers_path)
        self._servers: dict[str, ServerConfig] = {}
        self._health_status: dict[str, ServerHealth] = {}
        self._adapters: dict[str, Any] = {}  # Active MCP adapters
        self._health_check_tasks: dict[str, asyncio.Task] = {}

    def register_server(
        self,
        server_id: str,
        name: str,
        description: str = "",
        endpoint: str | None = None,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        health_check_interval: int = 60,
        enabled: bool = True,
    ) -> None:
        """
        Register MCP server configuration

        Args:
            server_id: Unique server identifier
            name: Human-readable server name
            description: Server description
            endpoint: Server endpoint (None for local servers)
            max_retries: Maximum retry attempts
            timeout_seconds: Request timeout
            health_check_interval: Health check interval in seconds
            enabled: Whether server is enabled
        """
        config = ServerConfig(
            server_id=server_id,
            name=name,
            description=description,
            endpoint=endpoint,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            health_check_interval=health_check_interval,
            enabled=enabled,
        )

        self._servers[server_id] = config
        self._health_status[server_id] = ServerHealth(
            server_id=server_id,
            status=ServerStatus.UNKNOWN,
            last_check=datetime.now(),
            response_time_ms=None,
        )

        # Start health check task
        if enabled and health_check_interval > 0:
            self._start_health_check(server_id)

        logger.info(f"Registered MCP server: {server_id} ({name})")

    def unregister_server(self, server_id: str) -> bool:
        """
        Unregister MCP server

        Args:
            server_id: Server identifier to unregister

        Returns:
            True if server was unregistered, False if not found
        """
        if server_id not in self._servers:
            return False

        # Stop health check task
        if server_id in self._health_check_tasks:
            self._health_check_tasks[server_id].cancel()
            del self._health_check_tasks[server_id]

        # Remove server
        del self._servers[server_id]
        del self._health_status[server_id]

        logger.info(f"Unregistered MCP server: {server_id}")
        return True

    async def execute(
        self,
        server_id: str,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute request on MCP server with retry logic

        Args:
            server_id: Server identifier
            method: Method to call on server
            params: Method parameters
            timeout: Request timeout (overrides server default)

        Returns:
            Dict with execution result

        Raises:
            ValueError: If server not found or disabled
            TimeoutError: If request times out
            ConnectionError: If server unavailable after retries
        """
        if server_id not in self._servers:
            raise ValueError(f"Server '{server_id}' not registered")

        config = self._servers[server_id]

        if not config.enabled:
            raise ValueError(f"Server '{server_id}' is disabled")

        # Check health status
        health = self._health_status[server_id]
        if health.status == ServerStatus.UNAVAILABLE:
            raise ConnectionError(f"Server '{server_id}' is unavailable: {health.error_message}")

        timeout_seconds = timeout if timeout is not None else config.timeout_seconds

        # Execute with retry logic
        for attempt in range(config.max_retries + 1):
            try:
                result = await self._execute_request(server_id, method, params, timeout_seconds)

                # Update health status on success
                self._health_status[server_id] = ServerHealth(
                    server_id=server_id,
                    status=ServerStatus.HEALTHY,
                    last_check=datetime.now(),
                    response_time_ms=None,  # TODO: Track actual response time
                )

                return result

            except TimeoutError as timeout_err:
                if attempt == config.max_retries:
                    logger.error(
                        f"Request to {server_id}.{method} timed out after "
                        f"{config.max_retries} retries"
                    )
                    raise TimeoutError(
                        f"Request to {server_id}.{method} timed out"
                    ) from timeout_err

                # Exponential backoff
                wait_time = 2**attempt
                logger.warning(
                    f"Request to {server_id}.{method} timed out "
                    f"(attempt {attempt + 1}/{config.max_retries + 1}), "
                    f"retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)

            except Exception as e:
                if attempt == config.max_retries:
                    logger.error(
                        f"Request to {server_id}.{method} failed after "
                        f"{config.max_retries} retries: {e}"
                    )
                    self._health_status[server_id] = ServerHealth(
                        server_id=server_id,
                        status=ServerStatus.DEGRADED,
                        last_check=datetime.now(),
                        response_time_ms=None,
                        error_message=str(e),
                    )
                    raise ConnectionError(f"Request to {server_id}.{method} failed: {e}") from e

                # Exponential backoff
                wait_time = 2**attempt
                logger.warning(
                    f"Request to {server_id}.{method} failed "
                    f"(attempt {attempt + 1}/{config.max_retries + 1}): {e}, "
                    f"retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)

        # Should never reach here
        raise ConnectionError(f"Request to {server_id}.{method} failed")

    async def _execute_request(
        self, server_id: str, method: str, params: dict | None, timeout: int
    ) -> dict[str, Any]:
        """
        Execute single request to MCP server using appropriate adapter

        Args:
            server_id: Server identifier
            method: Method to call
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Dict with execution result

        Raises:
            ValueError: If server or method not supported
            ConnectionError: If adapter fails
        """
        logger.info(f"Executing {server_id}.{method} with params: {params}")

        # Get or create adapter for this server
        adapter = await self._get_or_create_adapter(server_id, timeout)

        # Route to appropriate adapter method
        try:
            if server_id == "bge_search":
                result = await self._execute_bge_method(adapter, method, params or {})
            elif server_id == "entscheidsuche":
                result = await self._execute_entscheidsuche_method(adapter, method, params or {})
            elif server_id == "cantonal_courts":
                result = await self._execute_cantonal_method(adapter, method, params or {})
            else:
                raise ValueError(f"Unsupported MCP server: {server_id}")

            return {
                "success": True,
                "server_id": server_id,
                "method": method,
                "result": result,
                "metadata": {"timestamp": datetime.now().isoformat()},
            }

        except Exception as e:
            logger.error(f"MCP adapter execution failed: {e}")
            raise ConnectionError(f"MCP execution failed: {e}") from e

    async def _get_or_create_adapter(self, server_id: str, timeout: int) -> Any:
        """Get existing adapter or create new one"""
        if server_id in self._adapters:
            adapter = self._adapters[server_id]
            # Check if adapter is still connected
            if hasattr(adapter, "client") and adapter.client.is_connected():
                return adapter

        # Create new adapter
        config = self._servers.get(server_id)
        if not config:
            raise ValueError(f"Server {server_id} not registered")

        # Determine command to start MCP server
        server_path = self.mcp_servers_path / server_id.replace("_", "-")
        command = ["node", str(server_path / "dist" / "index.js")]

        # Create appropriate adapter
        if server_id == "bge_search":
            adapter = BGESearchAdapter(command=command, timeout=timeout)
        elif server_id == "entscheidsuche":
            adapter = EntscheidausucheAdapter(command=command, timeout=timeout)
        elif server_id == "cantonal_courts":
            adapter = CantonalCourtsAdapter(command=command, timeout=timeout)
        else:
            raise ValueError(f"Unknown server type: {server_id}")

        # Connect adapter
        await adapter.connect()
        self._adapters[server_id] = adapter

        return adapter

    async def _execute_bge_method(
        self, adapter: BGESearchAdapter, method: str, params: dict[str, Any]
    ) -> Any:
        """Execute method on BGE Search adapter"""
        if method == "search":
            result = await adapter.search(**params)
            return {
                "query": result.query,
                "total_results": result.total_results,
                "decisions": [
                    {
                        "citation": d.citation,
                        "title": d.title,
                        "date": d.date.isoformat(),
                        "summary": d.summary,
                        "language": d.language,
                    }
                    for d in result.decisions
                ],
            }
        elif method == "get_decision":
            decision = await adapter.get_decision(params["citation"])
            if decision:
                return {
                    "found": True,
                    "citation": decision.citation,
                    "title": decision.title,
                    "summary": decision.summary,
                }
            return {"found": False}
        elif method == "validate_citation":
            return await adapter.validate_citation(params["citation"])
        else:
            raise ValueError(f"Unknown BGE method: {method}")

    async def _execute_entscheidsuche_method(
        self, adapter: EntscheidausucheAdapter, method: str, params: dict[str, Any]
    ) -> Any:
        """Execute method on Entscheidsuche adapter"""
        if method == "search":
            result = await adapter.search(**params)
            return {
                "query": result.query,
                "total_results": result.total_results,
                "decisions": [
                    {
                        "decision_id": d.decision_id,
                        "court_name": d.court_name,
                        "title": d.title,
                        "date": d.date.isoformat(),
                        "summary": d.summary,
                    }
                    for d in result.decisions
                ],
            }
        elif method == "get_decision":
            decision = await adapter.get_decision(params["decision_id"])
            if decision:
                return {
                    "found": True,
                    "decision_id": decision.decision_id,
                    "title": decision.title,
                    "summary": decision.summary,
                }
            return {"found": False}
        else:
            raise ValueError(f"Unknown Entscheidsuche method: {method}")

    async def _execute_cantonal_method(
        self, adapter: CantonalCourtsAdapter, method: str, params: dict[str, Any]
    ) -> Any:
        """Execute method on Cantonal Courts adapter"""
        if method == "search":
            result = await adapter.search(**params)
            return {
                "query": result.query,
                "cantons_searched": result.cantons_searched,
                "total_results": result.total_results,
                "decisions": [
                    {
                        "decision_id": d.decision_id,
                        "canton": d.canton,
                        "court_name": d.court.name,
                        "title": d.title,
                        "date": d.date.isoformat(),
                        "summary": d.summary,
                    }
                    for d in result.decisions
                ],
            }
        elif method == "list_courts":
            courts = await adapter.list_courts(params.get("canton"))
            return {
                "courts": [
                    {
                        "canton": c.canton,
                        "name": c.name,
                        "court_type": c.court_type,
                        "languages": c.languages,
                    }
                    for c in courts
                ]
            }
        else:
            raise ValueError(f"Unknown Cantonal Courts method: {method}")

    async def check_health(self, server_id: str) -> ServerHealth:
        """
        Check health of specific MCP server

        Args:
            server_id: Server identifier

        Returns:
            ServerHealth with current status
        """
        if server_id not in self._servers:
            raise ValueError(f"Server '{server_id}' not registered")

        start_time = datetime.now()

        try:
            # TODO: Replace with actual MCP health check
            # For now, simulate health check
            await asyncio.sleep(0.05)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            health = ServerHealth(
                server_id=server_id,
                status=ServerStatus.HEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
            )

        except Exception as e:
            health = ServerHealth(
                server_id=server_id,
                status=ServerStatus.UNAVAILABLE,
                last_check=datetime.now(),
                response_time_ms=None,
                error_message=str(e),
            )

        self._health_status[server_id] = health
        return health

    def get_health_status(self, server_id: str) -> ServerHealth:
        """
        Get cached health status for server

        Args:
            server_id: Server identifier

        Returns:
            ServerHealth with last known status
        """
        if server_id not in self._health_status:
            raise ValueError(f"Server '{server_id}' not registered")

        return self._health_status[server_id]

    def get_all_health_status(self) -> list[ServerHealth]:
        """
        Get health status for all registered servers

        Returns:
            List of ServerHealth for all servers
        """
        return list(self._health_status.values())

    def _start_health_check(self, server_id: str) -> None:
        """Start periodic health check task for server"""

        async def health_check_loop() -> None:
            config = self._servers[server_id]
            while True:
                await asyncio.sleep(config.health_check_interval)
                try:
                    await self.check_health(server_id)
                except Exception as e:
                    logger.error(f"Health check failed for {server_id}: {e}")

        task = asyncio.create_task(health_check_loop())
        self._health_check_tasks[server_id] = task

    async def shutdown(self) -> None:
        """Shutdown connection manager and cleanup resources"""
        # Disconnect all active adapters
        for server_id, adapter in self._adapters.items():
            try:
                logger.info(f"Disconnecting adapter: {server_id}")
                await adapter.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting {server_id}: {e}")

        self._adapters.clear()

        # Cancel all health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._health_check_tasks.values(), return_exceptions=True)

        logger.info("MCP Connection Manager shut down")
