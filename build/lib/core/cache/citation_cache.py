"""
Citation cache for BetterCallClaude v2.0

This module provides a SQLite-based caching layer for legal citations
with 24-hour TTL to reduce API calls to MCP servers.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast


class CitationCache:
    """
    SQLite-based cache for legal citation data

    Features:
    - 24-hour TTL for cached entries
    - Automatic expiration cleanup
    - Query-based key generation
    - JSON serialization for complex data structures
    - Thread-safe operations

    Example:
        cache = CitationCache(db_path="./cache/citations.db")

        # Check cache
        result = cache.get("BGE 147 V 321")
        if result is None:
            result = fetch_from_mcp_server("BGE 147 V 321")
            cache.set("BGE 147 V 321", result, ttl_hours=24)

        # Clear expired entries
        cache.cleanup_expired()
    """

    def __init__(self, db_path: Path | None = None, ttl_hours: int = 24):
        """
        Initialize citation cache

        Args:
            db_path: Path to SQLite database file
                    (default: ./cache/citations.db)
            ttl_hours: Default TTL in hours (default: 24)
        """
        if db_path is None:
            cache_dir = Path.cwd() / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "citations.db"

        self.db_path = Path(db_path)
        self.ttl_hours = ttl_hours
        self._init_database()

    def _init_database(self) -> None:
        """Create cache table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS citation_cache (
                    cache_key TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
                """
            )
            # Create index on expiration for faster cleanup
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON citation_cache(expires_at)
                """
            )
            conn.commit()

    def _generate_cache_key(self, query: str, filters: dict | None = None) -> str:
        """
        Generate cache key from query and filters

        Args:
            query: Search query or citation
            filters: Optional filter parameters

        Returns:
            SHA-256 hash of query + filters
        """
        key_data: dict[str, Any] = {"query": query}
        if filters:
            key_data["filters"] = filters

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, query: str, filters: dict | None = None) -> dict[str, Any] | None:
        """
        Retrieve cached citation data

        Args:
            query: Search query or citation
            filters: Optional filter parameters

        Returns:
            Cached data dict or None if not found or expired
        """
        cache_key = self._generate_cache_key(query, filters)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT data, expires_at, hit_count
                FROM citation_cache
                WHERE cache_key = ?
                """,
                (cache_key,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            data_json, expires_at, hit_count = row
            expires_dt = datetime.fromisoformat(expires_at)

            # Check expiration
            if datetime.now() > expires_dt:
                # Entry expired, delete it
                conn.execute("DELETE FROM citation_cache WHERE cache_key = ?", (cache_key,))
                conn.commit()
                return None

            # Update hit count and last accessed
            conn.execute(
                """
                UPDATE citation_cache
                SET hit_count = hit_count + 1,
                    last_accessed = ?
                WHERE cache_key = ?
                """,
                (datetime.now().isoformat(), cache_key),
            )
            conn.commit()

            return cast(dict[str, Any], json.loads(data_json))

    def set(
        self,
        query: str,
        data: dict[str, Any],
        filters: dict | None = None,
        ttl_hours: int | None = None,
    ) -> None:
        """
        Store citation data in cache

        Args:
            query: Search query or citation
            data: Data to cache (must be JSON-serializable)
            filters: Optional filter parameters
            ttl_hours: TTL in hours (default: instance ttl_hours)
        """
        cache_key = self._generate_cache_key(query, filters)
        ttl = ttl_hours if ttl_hours is not None else self.ttl_hours

        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=ttl)

        data_json = json.dumps(data)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO citation_cache
                (cache_key, query, data, created_at, expires_at, hit_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    cache_key,
                    query,
                    data_json,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                    created_at.isoformat(),
                ),
            )
            conn.commit()

    def delete(self, query: str, filters: dict | None = None) -> bool:
        """
        Delete specific cache entry

        Args:
            query: Search query or citation
            filters: Optional filter parameters

        Returns:
            True if entry was deleted, False if not found
        """
        cache_key = self._generate_cache_key(query, filters)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM citation_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            return cursor.rowcount > 0

    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries

        Returns:
            Number of entries deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM citation_cache WHERE expires_at < ?",
                (datetime.now().isoformat(),),
            )
            conn.commit()
            return cursor.rowcount

    def clear_all(self) -> int:
        """
        Clear entire cache

        Returns:
            Number of entries deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM citation_cache")
            conn.commit()
            return cursor.rowcount

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache statistics:
                - total_entries: Total cache entries
                - expired_entries: Number of expired entries
                - total_hits: Sum of all hit counts
                - oldest_entry: Timestamp of oldest entry
                - newest_entry: Timestamp of newest entry
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN expires_at < ? THEN 1 ELSE 0 END) as expired,
                    SUM(hit_count) as total_hits,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest
                FROM citation_cache
                """,
                (datetime.now().isoformat(),),
            )
            row = cursor.fetchone()

            return {
                "total_entries": row[0] or 0,
                "expired_entries": row[1] or 0,
                "total_hits": row[2] or 0,
                "oldest_entry": row[3],
                "newest_entry": row[4],
            }

    def get_top_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get most frequently accessed queries

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of dicts with query and hit_count, sorted by hit_count desc
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT query, hit_count, last_accessed
                FROM citation_cache
                WHERE expires_at > ?
                ORDER BY hit_count DESC
                LIMIT ?
                """,
                (datetime.now().isoformat(), limit),
            )

            return [
                {"query": row[0], "hit_count": row[1], "last_accessed": row[2]}
                for row in cursor.fetchall()
            ]
