"""
Unit tests for Citation Cache

Tests the SQLite-based citation caching functionality.
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.core.cache import CitationCache


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create temporary database path for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_cache.db"
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    os.rmdir(temp_dir)


class TestCitationCache:
    """Test CitationCache functionality"""

    def test_initialization(self, temp_db_path: Path) -> None:
        """Test cache initializes with database"""
        CitationCache(db_path=temp_db_path)

        assert temp_db_path.exists()

    def test_set_and_get(self, temp_db_path: Path) -> None:
        """Test storing and retrieving cache entry"""
        cache = CitationCache(db_path=temp_db_path)

        data = {"citation": "BGE 147 V 321", "title": "Test Case"}
        cache.set("BGE 147 V 321", data)

        retrieved = cache.get("BGE 147 V 321")

        assert retrieved == data

    def test_get_nonexistent(self, temp_db_path: Path) -> None:
        """Test retrieving nonexistent entry returns None"""
        cache = CitationCache(db_path=temp_db_path)

        result = cache.get("nonexistent")

        assert result is None

    def test_set_with_filters(self, temp_db_path: Path) -> None:
        """Test caching with filter parameters"""
        cache = CitationCache(db_path=temp_db_path)

        data = {"results": ["result1", "result2"]}
        filters = {"jurisdiction": "federal", "date_from": "2020-01-01"}

        cache.set("test query", data, filters=filters)
        retrieved = cache.get("test query", filters=filters)

        assert retrieved == data

    def test_different_filters_different_keys(self, temp_db_path: Path) -> None:
        """Test same query with different filters creates different cache entries"""
        cache = CitationCache(db_path=temp_db_path)

        data1 = {"results": ["federal"]}
        data2 = {"results": ["cantonal"]}

        cache.set("test", data1, filters={"jurisdiction": "federal"})
        cache.set("test", data2, filters={"jurisdiction": "cantonal"})

        result1 = cache.get("test", filters={"jurisdiction": "federal"})
        result2 = cache.get("test", filters={"jurisdiction": "cantonal"})

        assert result1 == data1
        assert result2 == data2

    def test_ttl_expiration(self, temp_db_path: Path) -> None:
        """Test cache entries expire after TTL"""
        cache = CitationCache(db_path=temp_db_path, ttl_hours=0)  # Immediate expiration

        data = {"test": "data"}
        cache.set("test", data, ttl_hours=0)

        # Entry should be immediately expired
        result = cache.get("test")

        assert result is None

    def test_delete(self, temp_db_path: Path) -> None:
        """Test deleting cache entry"""
        cache = CitationCache(db_path=temp_db_path)

        cache.set("test", {"data": "value"})
        deleted = cache.delete("test")

        assert deleted is True
        assert cache.get("test") is None

    def test_delete_nonexistent(self, temp_db_path: Path) -> None:
        """Test deleting nonexistent entry returns False"""
        cache = CitationCache(db_path=temp_db_path)

        deleted = cache.delete("nonexistent")

        assert deleted is False

    def test_hit_count(self, temp_db_path: Path) -> None:
        """Test hit count increments on access"""
        cache = CitationCache(db_path=temp_db_path)

        cache.set("test", {"data": "value"})

        # Access multiple times
        cache.get("test")
        cache.get("test")
        cache.get("test")

        stats = cache.get_stats()
        assert stats["total_hits"] == 3

    def test_cleanup_expired(self, temp_db_path: Path) -> None:
        """Test cleanup removes expired entries"""
        cache = CitationCache(db_path=temp_db_path)

        # Add expired entry
        cache.set("expired", {"data": "old"}, ttl_hours=0)

        # Add valid entry
        cache.set("valid", {"data": "new"}, ttl_hours=24)

        cleaned = cache.cleanup_expired()

        assert cleaned >= 1  # At least one expired entry removed
        assert cache.get("valid") is not None

    def test_clear_all(self, temp_db_path: Path) -> None:
        """Test clearing entire cache"""
        cache = CitationCache(db_path=temp_db_path)

        cache.set("entry1", {"data": "1"})
        cache.set("entry2", {"data": "2"})

        cleared = cache.clear_all()

        assert cleared == 2
        assert cache.get("entry1") is None
        assert cache.get("entry2") is None

    def test_get_stats(self, temp_db_path: Path) -> None:
        """Test cache statistics"""
        cache = CitationCache(db_path=temp_db_path)

        cache.set("entry1", {"data": "1"})
        cache.set("entry2", {"data": "2"})
        cache.get("entry1")  # Increment hit count

        stats = cache.get_stats()

        assert stats["total_entries"] == 2
        assert stats["total_hits"] == 1
        assert stats["oldest_entry"] is not None
        assert stats["newest_entry"] is not None

    def test_get_top_queries(self, temp_db_path: Path) -> None:
        """Test retrieving most accessed queries"""
        cache = CitationCache(db_path=temp_db_path)

        cache.set("query1", {"data": "1"})
        cache.set("query2", {"data": "2"})

        # Access query1 more times
        cache.get("query1")
        cache.get("query1")
        cache.get("query2")

        top_queries = cache.get_top_queries(limit=2)

        assert len(top_queries) == 2
        assert top_queries[0]["query"] == "query1"  # Most accessed
        assert top_queries[0]["hit_count"] == 2
