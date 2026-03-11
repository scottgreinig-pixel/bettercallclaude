"""
Comprehensive integration tests for MCPConnectionManager

Tests the MCP connection manager functionality including:
- Server registration and unregistration
- Health check validation and monitoring
- Adapter creation and error handling
- Shutdown cleanup and resource management
- Concurrent request handling
- Retry logic and timeout management
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.mcp.connection_manager import (
    MCPConnectionManager,
    ServerHealth,
    ServerStatus,
)


class TestConnectionManagerServerManagement:
    """Test server registration and management"""

    def test_register_server_creates_config(self) -> None:
        """Test server registration creates proper configuration"""
        manager = MCPConnectionManager()

        # Patch _start_health_check to avoid event loop issues in sync test
        with patch.object(manager, "_start_health_check"):
            manager.register_server(
                server_id="test_server",
                name="Test Server",
                description="Test description",
                endpoint="mcp://test",
                max_retries=5,
                timeout_seconds=45,
                health_check_interval=120,
                enabled=True,
            )

        assert "test_server" in manager._servers
        config = manager._servers["test_server"]
        assert config.server_id == "test_server"
        assert config.name == "Test Server"
        assert config.description == "Test description"
        assert config.endpoint == "mcp://test"
        assert config.max_retries == 5
        assert config.timeout_seconds == 45
        assert config.health_check_interval == 120
        assert config.enabled is True

    def test_register_server_initializes_health_status(self) -> None:
        """Test server registration initializes health status"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,  # Disable to prevent health check task
        )

        assert "test_server" in manager._health_status
        health = manager._health_status["test_server"]
        assert health.server_id == "test_server"
        assert health.status == ServerStatus.UNKNOWN
        assert health.response_time_ms is None

    def test_register_server_starts_health_check_task(self) -> None:
        """Test server registration starts health check task when enabled"""
        manager = MCPConnectionManager()

        # Mock the health check task creation
        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.done.return_value = False
        mock_task.cancelled.return_value = False

        with patch.object(manager, "_start_health_check") as mock_start:
            # Simulate task creation by adding to manager's task dict
            def side_effect(server_id: str) -> None:
                manager._health_check_tasks[server_id] = mock_task

            mock_start.side_effect = side_effect

            manager.register_server(
                server_id="test_server",
                name="Test Server",
                enabled=True,
                health_check_interval=60,
            )

        # Health check task should be created
        assert "test_server" in manager._health_check_tasks
        task = manager._health_check_tasks["test_server"]
        assert isinstance(task, asyncio.Task)
        assert not task.done()

    def test_register_server_no_health_check_when_disabled(self) -> None:
        """Test no health check task created when server disabled"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,
        )

        # No health check task should be created
        assert "test_server" not in manager._health_check_tasks

    def test_register_server_no_health_check_when_interval_zero(self) -> None:
        """Test no health check task when interval is zero"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=True,
            health_check_interval=0,
        )

        # No health check task should be created
        assert "test_server" not in manager._health_check_tasks

    def test_unregister_server_removes_config(self) -> None:
        """Test unregistering server removes configuration"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,
        )

        result = manager.unregister_server("test_server")

        assert result is True
        assert "test_server" not in manager._servers
        assert "test_server" not in manager._health_status

    def test_unregister_server_cancels_health_check_task(self) -> None:
        """Test unregistering server cancels health check task"""
        manager = MCPConnectionManager()

        # Mock the health check task
        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.cancelled.return_value = False

        with patch.object(manager, "_start_health_check") as mock_start:
            # Simulate task creation by adding to manager's task dict
            def side_effect(server_id: str) -> None:
                manager._health_check_tasks[server_id] = mock_task

            mock_start.side_effect = side_effect

            manager.register_server(
                server_id="test_server",
                name="Test Server",
                enabled=True,
                health_check_interval=60,
            )

        task = manager._health_check_tasks["test_server"]
        result = manager.unregister_server("test_server")

        assert result is True
        assert "test_server" not in manager._health_check_tasks
        assert task.cancel.called  # type: ignore[attr-defined]

    def test_unregister_nonexistent_server_returns_false(self) -> None:
        """Test unregistering non-existent server returns False"""
        manager = MCPConnectionManager()

        result = manager.unregister_server("nonexistent")

        assert result is False


class TestConnectionManagerHealthChecks:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_check_health_updates_status(self) -> None:
        """Test check_health updates server health status"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,
        )

        health = await manager.check_health("test_server")

        assert health.server_id == "test_server"
        assert health.status == ServerStatus.HEALTHY
        assert health.response_time_ms is not None
        assert health.response_time_ms > 0
        assert health.error_message is None

    @pytest.mark.asyncio
    async def test_check_health_unregistered_server_raises(self) -> None:
        """Test check_health raises for unregistered server"""
        manager = MCPConnectionManager()

        with pytest.raises(ValueError, match="not registered"):
            await manager.check_health("nonexistent")

    @pytest.mark.asyncio
    async def test_check_health_tracks_response_time(self) -> None:
        """Test check_health tracks response time"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,
        )

        health = await manager.check_health("test_server")

        # Response time should be tracked (simulated sleep is 50ms)
        assert health.response_time_ms is not None
        assert health.response_time_ms >= 40  # Allow some variance

    def test_get_health_status_returns_cached_status(self) -> None:
        """Test get_health_status returns cached health status"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,
        )

        # Get cached status (should be UNKNOWN initially)
        health = manager.get_health_status("test_server")

        assert health.server_id == "test_server"
        assert health.status == ServerStatus.UNKNOWN

    def test_get_health_status_unregistered_raises(self) -> None:
        """Test get_health_status raises for unregistered server"""
        manager = MCPConnectionManager()

        with pytest.raises(ValueError, match="not registered"):
            manager.get_health_status("nonexistent")

    def test_get_all_health_status_returns_all_servers(self) -> None:
        """Test get_all_health_status returns all server statuses"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="server1",
            name="Server 1",
            enabled=False,
        )
        manager.register_server(
            server_id="server2",
            name="Server 2",
            enabled=False,
        )

        all_health = manager.get_all_health_status()

        assert len(all_health) == 2
        server_ids = {h.server_id for h in all_health}
        assert server_ids == {"server1", "server2"}


class TestConnectionManagerAdapterCreation:
    """Test adapter creation and error handling"""

    @pytest.mark.asyncio
    async def test_execute_creates_adapter_for_registered_server(self) -> None:
        """Test execute creates adapter for registered server"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
        )

        # Mock adapter creation and execution
        with patch("src.core.mcp.connection_manager.BGESearchAdapter") as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.client.is_connected.return_value = False
            mock_adapter.search.return_value = MagicMock(
                query="test",
                total_results=0,
                decisions=[],
            )
            mock_adapter_class.return_value = mock_adapter

            try:
                await manager.execute(
                    server_id="bge_search",
                    method="search",
                    params={"query": "test"},
                )
            except Exception:
                pass  # Expected to fail, we're testing adapter creation

            # Adapter should have been created
            assert mock_adapter_class.called
            assert mock_adapter.connect.called

    @pytest.mark.asyncio
    async def test_execute_unregistered_server_raises(self) -> None:
        """Test execute raises for unregistered server"""
        manager = MCPConnectionManager()

        with pytest.raises(ValueError, match="not registered"):
            await manager.execute(
                server_id="nonexistent",
                method="search",
                params={},
            )

    @pytest.mark.asyncio
    async def test_execute_disabled_server_raises(self) -> None:
        """Test execute raises for disabled server"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=False,
        )

        with pytest.raises(ValueError, match="is disabled"):
            await manager.execute(
                server_id="test_server",
                method="search",
                params={},
            )

    @pytest.mark.asyncio
    async def test_execute_unavailable_server_raises(self) -> None:
        """Test execute raises for unavailable server"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="test_server",
            name="Test Server",
            enabled=True,
        )

        # Manually set status to unavailable
        manager._health_status["test_server"] = ServerHealth(
            server_id="test_server",
            status=ServerStatus.UNAVAILABLE,
            last_check=datetime.now(),
            response_time_ms=None,
            error_message="Server down",
        )

        with pytest.raises(ConnectionError, match="is unavailable"):
            await manager.execute(
                server_id="test_server",
                method="search",
                params={},
            )

    @pytest.mark.asyncio
    async def test_get_or_create_adapter_reuses_connected_adapter(self) -> None:
        """Test adapter reuse when already connected"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
        )

        # Create mock adapter
        mock_adapter = AsyncMock()
        mock_adapter.client.is_connected.return_value = True

        # Store in adapter cache
        manager._adapters["bge_search"] = mock_adapter

        # Get adapter (should reuse existing)
        adapter = await manager._get_or_create_adapter("bge_search", 30)

        assert adapter is mock_adapter
        assert not mock_adapter.connect.called  # Should not reconnect

    @pytest.mark.asyncio
    async def test_get_or_create_adapter_unregistered_raises(self) -> None:
        """Test adapter creation raises for unregistered server"""
        manager = MCPConnectionManager()

        with pytest.raises(ValueError, match="not registered"):
            await manager._get_or_create_adapter("nonexistent", 30)


class TestConnectionManagerShutdown:
    """Test shutdown and cleanup functionality"""

    @pytest.mark.asyncio
    async def test_shutdown_disconnects_all_adapters(self) -> None:
        """Test shutdown disconnects all active adapters"""
        manager = MCPConnectionManager()

        # Create mock adapters
        mock_adapter1 = AsyncMock()
        mock_adapter2 = AsyncMock()

        manager._adapters["server1"] = mock_adapter1
        manager._adapters["server2"] = mock_adapter2

        await manager.shutdown()

        # Both adapters should be disconnected
        assert mock_adapter1.disconnect.called
        assert mock_adapter2.disconnect.called

        # Adapters cache should be cleared
        assert len(manager._adapters) == 0

    @pytest.mark.asyncio
    async def test_shutdown_cancels_health_check_tasks(self) -> None:
        """Test shutdown cancels all health check tasks"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="server1",
            name="Server 1",
            enabled=True,
            health_check_interval=60,
        )
        manager.register_server(
            server_id="server2",
            name="Server 2",
            enabled=True,
            health_check_interval=60,
        )

        task1 = manager._health_check_tasks["server1"]
        task2 = manager._health_check_tasks["server2"]

        await manager.shutdown()

        # Both tasks should be cancelled
        assert task1.cancelled()
        assert task2.cancelled()

    @pytest.mark.asyncio
    async def test_shutdown_handles_adapter_disconnect_errors(self) -> None:
        """Test shutdown handles errors during adapter disconnect"""
        manager = MCPConnectionManager()

        # Create mock adapter that raises on disconnect
        mock_adapter = AsyncMock()
        mock_adapter.disconnect.side_effect = Exception("Disconnect failed")

        manager._adapters["server1"] = mock_adapter

        # Shutdown should not raise even if adapter disconnect fails
        await manager.shutdown()

        # Adapter cache should still be cleared
        assert len(manager._adapters) == 0


class TestConnectionManagerRetryLogic:
    """Test retry logic and timeout handling"""

    @pytest.mark.asyncio
    async def test_execute_retries_on_timeout(self) -> None:
        """Test execute retries on timeout"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
            max_retries=2,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            # First two calls timeout, third succeeds
            mock_execute.side_effect = [
                TimeoutError(),
                TimeoutError(),
                {"success": True, "result": {}},
            ]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await manager.execute(
                    server_id="bge_search",
                    method="search",
                    params={},
                )

            # Should have retried twice then succeeded
            assert mock_execute.call_count == 3
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_raises_after_max_retries_timeout(self) -> None:
        """Test execute raises TimeoutError after max retries"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
            max_retries=2,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            # All calls timeout
            mock_execute.side_effect = TimeoutError()

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(TimeoutError, match="timed out"):
                    await manager.execute(
                        server_id="bge_search",
                        method="search",
                        params={},
                    )

            # Should have tried 3 times (initial + 2 retries)
            assert mock_execute.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_retries_on_connection_error(self) -> None:
        """Test execute retries on connection errors"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
            max_retries=2,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            # First two calls fail, third succeeds
            mock_execute.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                {"success": True, "result": {}},
            ]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await manager.execute(
                    server_id="bge_search",
                    method="search",
                    params={},
                )

            # Should have retried twice then succeeded
            assert mock_execute.call_count == 3
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_raises_after_max_retries_error(self) -> None:
        """Test execute raises ConnectionError after max retries"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
            max_retries=2,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            # All calls fail
            mock_execute.side_effect = Exception("Connection failed")

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(ConnectionError, match="failed"):
                    await manager.execute(
                        server_id="bge_search",
                        method="search",
                        params={},
                    )

            # Should have tried 3 times (initial + 2 retries)
            assert mock_execute.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_uses_exponential_backoff(self) -> None:
        """Test execute uses exponential backoff between retries"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
            max_retries=3,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Connection failed")

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                with pytest.raises(ConnectionError):
                    await manager.execute(
                        server_id="bge_search",
                        method="search",
                        params={},
                    )

                # Verify exponential backoff: 2^0=1s, 2^1=2s, 2^2=4s
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert sleep_calls == [1, 2, 4]

    @pytest.mark.asyncio
    async def test_execute_updates_health_on_success(self) -> None:
        """Test execute updates health status on successful request"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"success": True, "result": {}}

            await manager.execute(
                server_id="bge_search",
                method="search",
                params={},
            )

            # Health status should be updated to HEALTHY
            health = manager._health_status["bge_search"]
            assert health.status == ServerStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_execute_updates_health_on_failure(self) -> None:
        """Test execute updates health status on failed request"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
            max_retries=1,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Connection failed")

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(ConnectionError):
                    await manager.execute(
                        server_id="bge_search",
                        method="search",
                        params={},
                    )

            # Health status should be updated to DEGRADED
            health = manager._health_status["bge_search"]
            assert health.status == ServerStatus.DEGRADED
            assert health.error_message == "Connection failed"


class TestConnectionManagerConcurrentOperations:
    """Test concurrent request handling"""

    @pytest.mark.asyncio
    async def test_concurrent_requests_to_same_server(self) -> None:
        """Test handling concurrent requests to same server"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"success": True, "result": {}}

            # Execute 5 concurrent requests
            tasks = [
                manager.execute(
                    server_id="bge_search",
                    method="search",
                    params={"query": f"query{i}"},
                )
                for i in range(5)
            ]

            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert len(results) == 5
            assert all(r["success"] for r in results)

            # All requests should have been executed
            assert mock_execute.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_requests_to_different_servers(self) -> None:
        """Test handling concurrent requests to different servers"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            enabled=True,
        )
        manager.register_server(
            server_id="entscheidsuche",
            name="Entscheidsuche",
            enabled=True,
        )

        with patch.object(manager, "_execute_request", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"success": True, "result": {}}

            # Execute concurrent requests to different servers
            tasks = [
                manager.execute(
                    server_id="bge_search",
                    method="search",
                    params={},
                ),
                manager.execute(
                    server_id="entscheidsuche",
                    method="search",
                    params={},
                ),
                manager.execute(
                    server_id="bge_search",
                    method="search",
                    params={},
                ),
            ]

            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert len(results) == 3
            assert all(r["success"] for r in results)
