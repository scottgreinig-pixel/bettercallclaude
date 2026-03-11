"""
Integration tests for MCP Protocol Client

Tests the low-level MCP JSON-RPC 2.0 protocol implementation over stdio transport.
These tests verify that the MCPClient can:
- Start and connect to MCP server processes
- Perform initialize handshake
- Invoke tools with proper JSON-RPC formatting
- Handle responses and errors correctly
- Clean up resources properly
"""

import asyncio
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.mcp.protocol import MCPClient, MCPInvocationError, MCPProtocolError, MCPServerInfo


class TestMCPClientConnection:
    """Test MCP client connection lifecycle"""

    @pytest.mark.asyncio
    async def test_connect_starts_process(self) -> None:
        """Test that connect() starts MCP server process"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()

            # Verify process was started with correct command
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert call_args[0][0] == ["node", "test-server.js"]

    @pytest.mark.asyncio
    async def test_disconnect_terminates_process(self) -> None:
        """Test that disconnect() properly terminates MCP server process"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()
            await client.disconnect()

            # Verify process was terminated
            mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected_reflects_state(self) -> None:
        """Test that is_connected() accurately reflects connection state"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        # Before connection
        assert not client.is_connected()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process running
            mock_popen.return_value = mock_process

            await client.connect()

            # After connection
            assert client.is_connected()

            await client.disconnect()

            # After disconnection
            assert not client.is_connected()


class TestMCPClientInitialization:
    """Test MCP client initialization handshake"""

    @pytest.mark.asyncio
    async def test_initialize_handshake(self) -> None:
        """Test successful initialize handshake with MCP server"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_stdin = MagicMock()
            mock_stdout = MagicMock()

            # Mock initialize response
            init_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "test-server", "version": "1.0.0"},
                    "capabilities": {
                        "tools": {
                            "tools": [
                                {
                                    "name": "test_tool",
                                    "description": "A test tool",
                                    "inputSchema": {"type": "object"},
                                }
                            ]
                        }
                    },
                },
            }

            mock_stdout.readline.return_value = json.dumps(init_response) + "\n"
            mock_process.stdin = mock_stdin
            mock_process.stdout = mock_stdout
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()

            # Create async function that returns the response
            async def mock_read(func: Any) -> Any:
                return mock_stdout.readline()

            with patch("asyncio.to_thread", side_effect=mock_read):
                server_info = await client.initialize()

                # Verify initialize request was sent
                mock_stdin.write.assert_called_once()
                written_data = mock_stdin.write.call_args[0][0]
                request = json.loads(written_data.strip())

                assert request["jsonrpc"] == "2.0"
                assert request["method"] == "initialize"
                assert request["params"]["protocolVersion"] == "2024-11-05"
                assert request["params"]["clientInfo"]["name"] == "BetterCallClaude"

                # Verify server info was parsed correctly
                assert isinstance(server_info, MCPServerInfo)
                assert server_info.protocol_version == "2024-11-05"
                assert server_info.name == "test-server"
                assert len(server_info.capabilities) == 1
                assert server_info.capabilities[0].name == "test_tool"

    @pytest.mark.asyncio
    async def test_initialize_timeout(self) -> None:
        """Test that initialize times out if server doesn't respond"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=1)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_stdin = MagicMock()
            mock_stdout = MagicMock()

            # Mock timeout - readline never returns
            async def slow_readline(func: Any) -> str:
                await asyncio.sleep(10)
                return ""

            mock_process.stdin = mock_stdin
            mock_process.stdout = mock_stdout
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()

            with patch("asyncio.to_thread", side_effect=slow_readline):
                with pytest.raises(MCPProtocolError) as exc_info:
                    await client.initialize()

                assert "timeout" in str(exc_info.value).lower()


class TestMCPClientToolInvocation:
    """Test MCP client tool invocation"""

    @pytest.mark.asyncio
    async def test_invoke_tool_success(self) -> None:
        """Test successful tool invocation"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_stdin = MagicMock()
            mock_stdout = MagicMock()

            # Mock tool invocation response
            tool_response = {
                "jsonrpc": "2.0",
                "id": 1,  # First request after connect (connect doesn't send a request)
                "result": {"success": True, "data": {"result": "test result"}},
            }

            mock_stdout.readline.return_value = json.dumps(tool_response) + "\n"
            mock_process.stdin = mock_stdin
            mock_process.stdout = mock_stdout
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()

            # Create async function that returns the response
            async def mock_read(func: Any) -> Any:
                return mock_stdout.readline()

            with patch("asyncio.to_thread", side_effect=mock_read):
                result = await client.invoke_tool("test_tool", {"param1": "value1", "param2": 42})

                # Verify tool invocation request
                assert mock_stdin.write.call_count >= 1
                written_data = mock_stdin.write.call_args[0][0]
                request = json.loads(written_data.strip())

                assert request["jsonrpc"] == "2.0"
                assert request["method"] == "tools/call"
                assert request["params"]["name"] == "test_tool"
                assert request["params"]["arguments"]["param1"] == "value1"
                assert request["params"]["arguments"]["param2"] == 42

                # Verify result
                assert result["success"] is True
                assert result["data"]["result"] == "test result"

    @pytest.mark.asyncio
    async def test_invoke_tool_error(self) -> None:
        """Test tool invocation error handling"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_stdin = MagicMock()
            mock_stdout = MagicMock()

            # Mock error response
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,  # First request after connect
                "error": {"code": -32602, "message": "Invalid parameters"},
            }

            mock_stdout.readline.return_value = json.dumps(error_response) + "\n"
            mock_process.stdin = mock_stdin
            mock_process.stdout = mock_stdout
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()

            # Create async function that returns the response
            async def mock_read(func: Any) -> Any:
                return mock_stdout.readline()

            with patch("asyncio.to_thread", side_effect=mock_read):
                with pytest.raises(MCPInvocationError) as exc_info:
                    await client.invoke_tool("test_tool", {"invalid": "params"})

                assert "Invalid parameters" in str(exc_info.value)


class TestMCPClientResourceManagement:
    """Test MCP client resource management"""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager automatically connects and disconnects"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdin = MagicMock()
            mock_process.stdout = MagicMock()
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            # Initialize response for context manager
            init_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "test-server", "version": "1.0.0"},
                    "capabilities": {"tools": {"tools": []}},
                },
            }

            mock_process.stdout.readline.return_value = json.dumps(init_response) + "\n"

            # Create async function that returns the response
            async def mock_read(func: Any) -> Any:
                return mock_process.stdout.readline()

            with patch("asyncio.to_thread", side_effect=mock_read):
                async with client:
                    assert client.is_connected()

                # After context manager exit
                mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_requests_reuse_connection(self) -> None:
        """Test that multiple tool invocations reuse the same connection"""
        client = MCPClient(command=["node", "test-server.js"], server_id="test_server", timeout=5)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_stdin = MagicMock()
            mock_stdout = MagicMock()

            # Mock responses for multiple calls
            responses = [
                json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"data": "first"}}) + "\n",
                json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"data": "second"}}) + "\n",
                json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"data": "third"}}) + "\n",
            ]

            mock_stdout.readline.side_effect = responses
            mock_process.stdin = mock_stdin
            mock_process.stdout = mock_stdout
            mock_process.stderr = MagicMock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process

            await client.connect()

            # Create async function that yields responses in sequence
            call_count = 0

            async def mock_read(func: Any) -> Any:
                nonlocal call_count
                result = responses[call_count]
                call_count += 1
                return result

            with patch("asyncio.to_thread", side_effect=mock_read):
                _result1 = await client.invoke_tool("tool1", {})
                _result2 = await client.invoke_tool("tool2", {})
                _result3 = await client.invoke_tool("tool3", {})

                # Verify only one process was started
                assert mock_popen.call_count == 1

                # Verify all requests used the same stdin
                assert mock_stdin.write.call_count == 3
