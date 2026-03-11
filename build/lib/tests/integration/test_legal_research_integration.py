"""
End-to-end integration tests for Legal Research Command with MCP servers

Tests the complete integration flow from LegalResearchCommand through
ConnectionManager to MCP adapters. Verifies:
- Jurisdiction-based routing to correct MCP servers
- Multi-source search aggregation
- Error handling and partial failure recovery
- Result formatting and metadata
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.commands.legal_research import LegalResearchCommand
from src.core.mcp.connection_manager import MCPConnectionManager, ServerStatus


class TestLegalResearchIntegration:
    """Test end-to-end legal research integration"""

    @pytest.mark.asyncio
    async def test_federal_jurisdiction_searches_bge_only(self) -> None:
        """Test federal jurisdiction routes to BGE search only"""
        command = LegalResearchCommand()

        # Mock ConnectionManager
        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            # Mock BGE response
            mock_execute.return_value = {
                "success": True,
                "server_id": "bge_search",
                "method": "search",
                "result": {
                    "query": "test query",
                    "total_results": 2,
                    "decisions": [
                        {
                            "citation": "BGE 147 V 321",
                            "title": "Test Decision 1",
                            "date": "2021-09-15",
                            "summary": "Summary 1",
                            "language": "DE",
                        },
                        {
                            "citation": "BGE 146 II 150",
                            "title": "Test Decision 2",
                            "date": "2020-03-10",
                            "summary": "Summary 2",
                            "language": "FR",
                        },
                    ],
                },
                "metadata": {},
            }

            # Execute command with federal jurisdiction
            result = await command.execute(
                {"query": "test query", "jurisdiction": "federal", "limit": 10}
            )

            # Verify only BGE was called
            assert mock_execute.call_count == 1
            call_args = mock_execute.call_args
            assert call_args[1]["server_id"] == "bge_search"
            assert call_args[1]["method"] == "search"

            # Verify results
            assert result["success"] is True
            assert len(result["results"]) == 2
            assert result["results"][0]["citation"] == "BGE 147 V 321"
            assert result["results"][0]["court"] == "Bundesgericht (Federal Supreme Court)"
            assert result["sources"] == ["bge_search"]

    @pytest.mark.asyncio
    async def test_cantonal_jurisdiction_searches_entscheidsuche(self) -> None:
        """Test cantonal jurisdiction routes to Entscheidsuche with court level filter"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            # Mock Entscheidsuche response
            mock_execute.return_value = {
                "success": True,
                "server_id": "entscheidsuche",
                "method": "search",
                "result": {
                    "query": "test query",
                    "total_results": 1,
                    "decisions": [
                        {
                            "decision_id": "ZH-2023-001",
                            "title": "Cantonal Decision",
                            "court_name": "Obergericht Zürich",
                            "date": "2023-05-10",
                            "summary": "Cantonal court decision",
                        }
                    ],
                },
                "metadata": {},
            }

            result = await command.execute(
                {"query": "test query", "jurisdiction": "cantonal", "limit": 10}
            )

            # Verify Entscheidsuche was called with court_level filter
            assert mock_execute.call_count == 1
            call_args = mock_execute.call_args
            assert call_args[1]["server_id"] == "entscheidsuche"
            assert call_args[1]["params"]["court_level"] == "cantonal"

            # Verify results
            assert result["success"] is True
            assert len(result["results"]) == 1
            assert result["results"][0]["decision_id"] == "ZH-2023-001"
            assert result["sources"] == ["entscheidsuche"]

    @pytest.mark.asyncio
    async def test_all_jurisdiction_searches_multiple_sources(self) -> None:
        """Test 'all' jurisdiction searches both BGE and Entscheidsuche"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            # Mock responses from both sources
            def execute_side_effect(*args: Any, **kwargs: Any) -> dict[str, Any]:
                server_id = kwargs.get("server_id")
                if server_id == "bge_search":
                    return {
                        "success": True,
                        "result": {
                            "decisions": [
                                {
                                    "citation": "BGE 147 V 321",
                                    "title": "Federal Decision",
                                    "date": "2021-09-15",
                                    "summary": "Federal summary",
                                    "language": "DE",
                                }
                            ]
                        },
                    }
                elif server_id == "entscheidsuche":
                    return {
                        "success": True,
                        "result": {
                            "decisions": [
                                {
                                    "decision_id": "ZH-2023-001",
                                    "title": "Cantonal Decision",
                                    "court_name": "Obergericht Zürich",
                                    "date": "2023-05-10",
                                    "summary": "Cantonal summary",
                                }
                            ]
                        },
                    }
                else:
                    return {"success": False, "error": f"Unknown server_id: {server_id}"}

            mock_execute.side_effect = execute_side_effect

            result = await command.execute(
                {"query": "test query", "jurisdiction": "all", "limit": 10}
            )

            # Verify both sources were called
            assert mock_execute.call_count == 2
            server_ids_called = [call[1]["server_id"] for call in mock_execute.call_args_list]
            assert "bge_search" in server_ids_called
            assert "entscheidsuche" in server_ids_called

            # Verify results aggregated from both sources
            assert result["success"] is True
            assert len(result["results"]) == 2
            assert "bge_search" in result["sources"]
            assert "entscheidsuche" in result["sources"]

    @pytest.mark.asyncio
    async def test_date_filters_passed_to_mcp_servers(self) -> None:
        """Test date filters are correctly passed to MCP servers"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": {"decisions": []},
            }

            await command.execute(
                {
                    "query": "test",
                    "jurisdiction": "federal",
                    "date_from": "2020-01-01",
                    "date_to": "2023-12-31",
                    "limit": 10,
                }
            )

            # Verify date filters passed to MCP server
            call_args = mock_execute.call_args
            assert call_args[1]["params"]["date_from"] == "2020-01-01"
            assert call_args[1]["params"]["date_to"] == "2023-12-31"

    @pytest.mark.asyncio
    async def test_limit_parameter_passed_correctly(self) -> None:
        """Test limit parameter controls result count"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": {"decisions": [{"citation": f"BGE 147 V {i}"} for i in range(20)]},
            }

            result = await command.execute({"query": "test", "jurisdiction": "federal", "limit": 5})

            # Verify limit passed to MCP server
            call_args = mock_execute.call_args
            assert call_args[1]["params"]["limit"] == 5

            # Verify results limited
            assert len(result["results"]) <= 5


class TestErrorHandlingAndRecovery:
    """Test error handling and partial failure recovery"""

    @pytest.mark.asyncio
    async def test_bge_failure_continues_with_entscheidsuche(self) -> None:
        """Test that if BGE fails, Entscheidsuche still executes"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:

            def execute_with_bge_error(*args: Any, **kwargs: Any) -> dict[str, Any]:
                server_id = kwargs.get("server_id")
                if server_id == "bge_search":
                    raise Exception("BGE server unavailable")
                elif server_id == "entscheidsuche":
                    return {
                        "success": True,
                        "result": {
                            "decisions": [
                                {
                                    "decision_id": "ZH-2023-001",
                                    "title": "Working Decision",
                                    "court_name": "Obergericht Zürich",
                                    "date": "2023-05-10",
                                    "summary": "This still works",
                                }
                            ]
                        },
                    }
                else:
                    return {"success": False, "error": f"Unknown server_id: {server_id}"}

            mock_execute.side_effect = execute_with_bge_error

            result = await command.execute({"query": "test", "jurisdiction": "all", "limit": 10})

            # Verify execution continued despite BGE failure
            assert result["success"] is True
            assert len(result["results"]) == 1
            assert "entscheidsuche" in result["sources"]
            assert "bge_search (error:" in result["sources"][0]

    @pytest.mark.asyncio
    async def test_all_sources_fail_returns_empty_results(self) -> None:
        """Test that if all sources fail, returns success with empty results"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("All servers down")

            result = await command.execute({"query": "test", "jurisdiction": "all", "limit": 10})

            # Verify graceful handling
            assert result["success"] is True
            assert len(result["results"]) == 0
            assert all("error:" in source for source in result["sources"])

    @pytest.mark.asyncio
    async def test_connection_manager_shutdown_always_called(self) -> None:
        """Test ConnectionManager.shutdown() always called even on errors"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", side_effect=Exception("Error")):
            with patch.object(
                MCPConnectionManager, "shutdown", new_callable=AsyncMock
            ) as mock_shutdown:
                try:
                    await command.execute({"query": "test", "jurisdiction": "federal", "limit": 10})
                except Exception:
                    pass

                # Verify shutdown was called despite error
                mock_shutdown.assert_called_once()


class TestResultFormatting:
    """Test result formatting and metadata"""

    @pytest.mark.asyncio
    async def test_result_includes_execution_time(self) -> None:
        """Test result includes execution time in metadata"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": {"decisions": []},
            }

            result = await command.execute(
                {"query": "test", "jurisdiction": "federal", "limit": 10}
            )

            # Verify metadata includes execution time
            assert "execution_time_ms" in result["metadata"]
            assert isinstance(result["metadata"]["execution_time_ms"], (int, float))
            assert result["metadata"]["execution_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_result_includes_search_parameters(self) -> None:
        """Test result metadata includes all search parameters"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": {"decisions": []},
            }

            result = await command.execute(
                {
                    "query": "arbeitsrecht",
                    "jurisdiction": "cantonal",
                    "date_from": "2020-01-01",
                    "date_to": "2023-12-31",
                    "limit": 15,
                }
            )

            # Verify all parameters in metadata
            metadata = result["metadata"]
            assert metadata["query"] == "arbeitsrecht"
            assert metadata["jurisdiction"] == "cantonal"
            assert metadata["date_from"] == "2020-01-01"
            assert metadata["date_to"] == "2023-12-31"
            assert metadata["limit"] == 15

    @pytest.mark.asyncio
    async def test_result_includes_total_results_count(self) -> None:
        """Test result metadata includes total results before limit"""
        command = LegalResearchCommand()

        with patch.object(MCPConnectionManager, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": {
                    "decisions": [
                        {"citation": f"BGE 147 V {i}", "title": f"Decision {i}"} for i in range(20)
                    ]
                },
            }

            result = await command.execute({"query": "test", "jurisdiction": "federal", "limit": 5})

            # Verify total_results shows count before limit
            assert result["metadata"]["total_results"] == 20
            assert len(result["results"]) == 5  # Limited


class TestConnectionManagerIntegration:
    """Test ConnectionManager integration with adapters"""

    @pytest.mark.asyncio
    async def test_connection_manager_registers_servers(self) -> None:
        """Test ConnectionManager properly registers MCP servers"""
        manager = MCPConnectionManager()

        # Register servers
        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            description="Federal Supreme Court decisions",
        )

        manager.register_server(
            server_id="entscheidsuche",
            name="Entscheidsuche",
            description="Court decision search",
        )

        # Verify servers registered
        assert "bge_search" in manager._servers
        assert "entscheidsuche" in manager._servers
        assert manager._servers["bge_search"].name == "BGE Search"

    @pytest.mark.asyncio
    async def test_connection_manager_health_check(self) -> None:
        """Test ConnectionManager tracks health status"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            description="Federal Supreme Court decisions",
        )

        # Get health status
        health = manager.get_health_status("bge_search")

        # Verify health status structure
        assert health.server_id == "bge_search"
        assert health.status == ServerStatus.UNKNOWN  # Before first check

    @pytest.mark.asyncio
    async def test_connection_manager_adapter_reuse(self) -> None:
        """Test ConnectionManager reuses adapters for same server"""
        manager = MCPConnectionManager()

        manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            description="Federal Supreme Court decisions",
        )

        with patch("src.core.mcp.connection_manager.BGESearchAdapter") as MockAdapter:
            mock_adapter_instance = AsyncMock()
            mock_adapter_instance.connect = AsyncMock()  # Mock the connect method
            mock_adapter_instance.client = MagicMock()
            mock_adapter_instance.client.is_connected.return_value = True
            mock_adapter_instance.search.return_value = AsyncMock(
                query="test", total_results=0, decisions=[]
            )
            MockAdapter.return_value = mock_adapter_instance

            # First request - creates adapter
            await manager._get_or_create_adapter("bge_search", timeout=30)

            # Second request - reuses adapter
            await manager._get_or_create_adapter("bge_search", timeout=30)

            # Verify adapter created only once
            assert MockAdapter.call_count == 1
