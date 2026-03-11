"""
Integration tests for MCP Adapters

Tests the high-level domain-specific adapters for BGE, Entscheidsuche, and
Cantonal Courts. Verifies that adapters correctly:
- Transform domain parameters to MCP tool invocations
- Parse MCP responses into domain objects
- Handle Swiss legal domain specifics (citations, court hierarchy, cantons)
- Manage connection lifecycle
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.mcp.adapters import (
    BGESearchAdapter,
    CantonalCourtsAdapter,
    EntscheidausucheAdapter,
)
from src.core.mcp.adapters.bge_search import BGEDecision, BGESearchResult
from src.core.mcp.adapters.cantonal_courts import (
    SWISS_CANTONS,
    CantonalCourt,
    CantonalDecision,
    CantonalSearchResult,
)
from src.core.mcp.adapters.entscheidsuche import (
    CourtDecision,
    EntscheidausucheSearchResult,
)


class TestBGESearchAdapter:
    """Test BGE Search adapter functionality"""

    @pytest.mark.asyncio
    async def test_search_builds_correct_parameters(self) -> None:
        """Test that search() builds correct MCP tool parameters"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        # Mock the client
        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [],
            "totalResults": 0,
            "searchTimeMs": 100.0,
            "metadata": {},
        }
        adapter.client = mock_client

        # Execute search with all parameters
        await adapter.search(
            query="sozialversicherung",
            language="DE",
            date_from="2020-01-01",
            date_to="2023-12-31",
            chambers=["V", "II"],
            legal_areas=["Sozialversicherungsrecht"],
            limit=20,
        )

        # Verify invoke_tool was called with correct parameters
        mock_client.invoke_tool.assert_called_once_with(
            "search_bge",
            {
                "query": "sozialversicherung",
                "language": "DE",
                "dateFrom": "2020-01-01",
                "dateTo": "2023-12-31",
                "chambers": ["V", "II"],
                "legalAreas": ["Sozialversicherungsrecht"],
                "limit": 20,
            },
        )

    @pytest.mark.asyncio
    async def test_search_parses_decisions(self) -> None:
        """Test that search() correctly parses BGE decisions"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        # Mock the client with realistic BGE response
        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [
                {
                    "citation": "BGE 147 V 321",
                    "volume": "147",
                    "chamber": "V",
                    "page": "321",
                    "title": "Invalidenversicherung",
                    "date": "2021-09-15T00:00:00Z",
                    "language": "DE",
                    "summary": "Decision about disability insurance",
                    "legalAreas": ["Sozialversicherungsrecht"],
                    "fullTextUrl": "https://www.bger.ch/...",
                }
            ],
            "totalResults": 1,
            "searchTimeMs": 150.5,
            "metadata": {},
        }
        adapter.client = mock_client

        result = await adapter.search(query="test")

        # Verify result structure
        assert isinstance(result, BGESearchResult)
        assert result.query == "test"
        assert result.total_results == 1
        assert len(result.decisions) == 1

        # Verify decision parsing
        decision = result.decisions[0]
        assert isinstance(decision, BGEDecision)
        assert decision.citation == "BGE 147 V 321"
        assert decision.volume == "147"
        assert decision.chamber == "V"
        assert decision.page == "321"
        assert decision.title == "Invalidenversicherung"
        assert isinstance(decision.date, datetime)
        assert decision.language == "DE"
        assert decision.summary == "Decision about disability insurance"

    @pytest.mark.asyncio
    async def test_get_decision(self) -> None:
        """Test get_decision() retrieves specific BGE decision"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "found": True,
            "decision": {
                "citation": "BGE 147 V 321",
                "volume": "147",
                "chamber": "V",
                "page": "321",
                "title": "Test Decision",
                "date": "2021-09-15T00:00:00Z",
                "language": "DE",
                "summary": "Test summary",
                "legalAreas": [],
            },
        }
        adapter.client = mock_client

        decision = await adapter.get_decision("BGE 147 V 321")

        # Verify tool invocation
        mock_client.invoke_tool.assert_called_once_with(
            "get_bge_decision", {"citation": "BGE 147 V 321"}
        )

        # Verify decision returned
        assert decision is not None
        assert decision.citation == "BGE 147 V 321"

    @pytest.mark.asyncio
    async def test_get_decision_not_found(self) -> None:
        """Test get_decision() returns None when decision not found"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {"found": False}
        adapter.client = mock_client

        decision = await adapter.get_decision("BGE 999 X 999")

        assert decision is None

    @pytest.mark.asyncio
    async def test_validate_citation(self) -> None:
        """Test validate_citation() validates BGE citation format"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "valid": True,
            "volume": "147",
            "chamber": "V",
            "page": "321",
            "normalized": "BGE 147 V 321",
        }
        adapter.client = mock_client

        result = await adapter.validate_citation("BGE 147 V 321")

        # Verify validation result
        assert result["valid"] is True
        assert result["volume"] == "147"
        assert result["chamber"] == "V"
        assert result["page"] == "321"


class TestEntscheidausucheAdapter:
    """Test Entscheidsuche adapter functionality"""

    @pytest.mark.asyncio
    async def test_search_with_court_level_filter(self) -> None:
        """Test search() with court level filtering"""
        adapter = EntscheidausucheAdapter(command=["node", "entscheid-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [],
            "totalResults": 0,
            "facets": {},
            "searchTimeMs": 100.0,
            "metadata": {},
        }
        adapter.client = mock_client

        await adapter.search(
            query="arbeitsrecht", court_level="cantonal", canton="ZH", language="DE"
        )

        # Verify court level filter passed correctly
        mock_client.invoke_tool.assert_called_once()
        call_args = mock_client.invoke_tool.call_args
        assert call_args[0][1]["courtLevel"] == "cantonal"
        assert call_args[0][1]["canton"] == "ZH"
        assert call_args[0][1]["language"] == "DE"

    @pytest.mark.asyncio
    async def test_search_parses_court_decisions(self) -> None:
        """Test search() parses court decisions correctly"""
        adapter = EntscheidausucheAdapter(command=["node", "entscheid-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [
                {
                    "decisionId": "ZH-2023-001",
                    "courtName": "Obergericht Zürich",
                    "courtLevel": "cantonal",
                    "canton": "ZH",
                    "title": "Arbeitsrecht Entscheid",
                    "date": "2023-03-15T00:00:00Z",
                    "language": "DE",
                    "summary": "Employment law decision",
                    "legalAreas": ["Arbeitsrecht"],
                    "referenceNumber": "LA220050",
                }
            ],
            "totalResults": 1,
            "facets": {},
            "searchTimeMs": 200.0,
            "metadata": {},
        }
        adapter.client = mock_client

        result = await adapter.search(query="test")

        # Verify result
        assert isinstance(result, EntscheidausucheSearchResult)
        assert len(result.decisions) == 1

        decision = result.decisions[0]
        assert isinstance(decision, CourtDecision)
        assert decision.decision_id == "ZH-2023-001"
        assert decision.court_name == "Obergericht Zürich"
        assert decision.court_level == "cantonal"
        assert decision.canton == "ZH"

    @pytest.mark.asyncio
    async def test_get_related_decisions(self) -> None:
        """Test get_related_decisions() retrieves related decisions"""
        adapter = EntscheidausucheAdapter(command=["node", "entscheid-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "relatedDecisions": [
                {
                    "decisionId": "ZH-2023-002",
                    "courtName": "Obergericht Zürich",
                    "courtLevel": "cantonal",
                    "canton": "ZH",
                    "title": "Related Decision",
                    "date": "2023-04-01T00:00:00Z",
                    "language": "DE",
                    "summary": "Related case",
                    "legalAreas": ["Arbeitsrecht"],
                    "referenceNumber": "LA220051",
                }
            ]
        }
        adapter.client = mock_client

        related = await adapter.get_related_decisions("ZH-2023-001", limit=5)

        # Verify tool invocation
        mock_client.invoke_tool.assert_called_once_with(
            "get_related_decisions", {"decisionId": "ZH-2023-001", "limit": 5}
        )

        # Verify results
        assert len(related) == 1
        assert related[0].decision_id == "ZH-2023-002"


class TestCantonalCourtsAdapter:
    """Test Cantonal Courts adapter functionality"""

    @pytest.mark.asyncio
    async def test_search_validates_canton_codes(self) -> None:
        """Test search() validates Swiss canton codes"""
        adapter = CantonalCourtsAdapter(command=["node", "cantonal-server.js"], timeout=5)

        # Invalid canton code should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await adapter.search(query="test", cantons=["INVALID", "ZH"])

        assert "Invalid canton codes: ['INVALID']" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_all_cantons(self) -> None:
        """Test search() searches all 26 cantons when no filter"""
        adapter = CantonalCourtsAdapter(command=["node", "cantonal-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [],
            "totalResults": 0,
            "byCanton": {},
            "searchTimeMs": 500.0,
            "metadata": {},
        }
        adapter.client = mock_client

        await adapter.search(query="test")

        # Verify all 26 cantons were searched
        call_args = mock_client.invoke_tool.call_args
        assert call_args[0][1]["cantons"] == SWISS_CANTONS
        assert len(call_args[0][1]["cantons"]) == 26

    @pytest.mark.asyncio
    async def test_search_specific_cantons(self) -> None:
        """Test search() filters by specific cantons"""
        adapter = CantonalCourtsAdapter(command=["node", "cantonal-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [],
            "totalResults": 0,
            "byCanton": {},
            "searchTimeMs": 200.0,
            "metadata": {},
        }
        adapter.client = mock_client

        # Search only Zurich and Geneva
        await adapter.search(query="test", cantons=["ZH", "GE"])

        call_args = mock_client.invoke_tool.call_args
        assert call_args[0][1]["cantons"] == ["ZH", "GE"]

    @pytest.mark.asyncio
    async def test_search_parses_cantonal_decisions(self) -> None:
        """Test search() parses cantonal decisions with court info"""
        adapter = CantonalCourtsAdapter(command=["node", "cantonal-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [
                {
                    "decisionId": "ZH-OG-2023-001",
                    "canton": "ZH",
                    "court": {
                        "canton": "ZH",
                        "name": "Obergericht",
                        "courtType": "supreme",
                        "languages": ["DE"],
                        "websiteUrl": "https://www.zh.ch/obergericht",
                    },
                    "title": "Cantonal Decision",
                    "date": "2023-05-10T00:00:00Z",
                    "language": "DE",
                    "summary": "Test cantonal decision",
                    "legalAreas": ["Zivilrecht"],
                    "caseNumber": "ZH-2023-001",
                }
            ],
            "totalResults": 1,
            "byCanton": {"ZH": 1},
            "searchTimeMs": 150.0,
            "metadata": {},
        }
        adapter.client = mock_client

        result = await adapter.search(query="test", cantons=["ZH"])

        # Verify result parsing
        assert isinstance(result, CantonalSearchResult)
        assert len(result.decisions) == 1
        assert result.cantons_searched == ["ZH"]
        assert result.by_canton == {"ZH": 1}

        decision = result.decisions[0]
        assert isinstance(decision, CantonalDecision)
        assert decision.canton == "ZH"
        assert isinstance(decision.court, CantonalCourt)
        assert decision.court.name == "Obergericht"
        assert decision.court.court_type == "supreme"

    @pytest.mark.asyncio
    async def test_list_courts(self) -> None:
        """Test list_courts() retrieves cantonal court information"""
        adapter = CantonalCourtsAdapter(command=["node", "cantonal-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "courts": [
                {
                    "canton": "ZH",
                    "name": "Obergericht Zürich",
                    "courtType": "supreme",
                    "languages": ["DE"],
                    "websiteUrl": "https://www.zh.ch/obergericht",
                },
                {
                    "canton": "ZH",
                    "name": "Bezirksgericht Zürich",
                    "courtType": "district",
                    "languages": ["DE"],
                },
            ]
        }
        adapter.client = mock_client

        courts = await adapter.list_courts(canton="ZH")

        # Verify tool invocation
        mock_client.invoke_tool.assert_called_once_with("list_cantonal_courts", {"canton": "ZH"})

        # Verify court parsing
        assert len(courts) == 2
        assert all(isinstance(c, CantonalCourt) for c in courts)
        assert courts[0].canton == "ZH"
        assert courts[0].court_type == "supreme"

    @pytest.mark.asyncio
    async def test_list_courts_invalid_canton(self) -> None:
        """Test list_courts() rejects invalid canton code"""
        adapter = CantonalCourtsAdapter(command=["node", "cantonal-server.js"], timeout=5)

        with pytest.raises(ValueError) as exc_info:
            await adapter.list_courts(canton="INVALID")

        assert "Invalid canton code: INVALID" in str(exc_info.value)


class TestAdapterConnectionLifecycle:
    """Test adapter connection lifecycle management"""

    @pytest.mark.asyncio
    async def test_adapter_context_manager(self) -> None:
        """Test adapters work as async context managers"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        # Mock the underlying client
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.initialize = AsyncMock()
        mock_client.disconnect = AsyncMock()
        adapter.client = mock_client

        async with adapter:
            # Verify connect and initialize were called
            mock_client.connect.assert_called_once()
            mock_client.initialize.assert_called_once()

        # Verify disconnect was called on exit
        mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_searches_reuse_connection(self) -> None:
        """Test multiple searches reuse the same adapter connection"""
        adapter = BGESearchAdapter(command=["node", "bge-server.js"], timeout=5)

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = {
            "decisions": [],
            "totalResults": 0,
            "searchTimeMs": 100.0,
            "metadata": {},
        }
        adapter.client = mock_client

        # Perform multiple searches
        await adapter.search(query="query1")
        await adapter.search(query="query2")
        await adapter.search(query="query3")

        # Verify all searches used the same client
        assert mock_client.invoke_tool.call_count == 3
