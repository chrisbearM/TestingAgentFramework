"""
Document Cache Manager
Stores processed document attachments in memory with TTL for session-based access
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock


class DocumentCache:
    """
    In-memory cache for processed document attachments.
    Stores documents by epic_key with automatic expiration.
    """

    def __init__(self, ttl_hours: int = 2):
        """
        Initialize document cache.

        Args:
            ttl_hours: Time-to-live in hours (default: 2 hours)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ttl = timedelta(hours=ttl_hours)

    def store(
        self,
        epic_key: str,
        epic_attachments: List[Dict[str, Any]],
        child_attachments: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """
        Store processed attachments for an epic.

        Args:
            epic_key: Epic identifier
            epic_attachments: List of processed epic attachments
            child_attachments: Dict mapping child keys to their attachments
        """
        with self._lock:
            self._cache[epic_key] = {
                'epic_attachments': epic_attachments,
                'child_attachments': child_attachments,
                'stored_at': datetime.now(),
                'expires_at': datetime.now() + self._ttl
            }
            print(f"DEBUG DocumentCache: Stored {len(epic_attachments)} epic attachments and {len(child_attachments)} child attachment sets for {epic_key}")

    def get(self, epic_key: str) -> Optional[Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]]:
        """
        Retrieve processed attachments for an epic.

        Args:
            epic_key: Epic identifier

        Returns:
            Tuple of (epic_attachments, child_attachments) if found and not expired, None otherwise
        """
        with self._lock:
            if epic_key not in self._cache:
                print(f"DEBUG DocumentCache: Cache miss for {epic_key}")
                return None

            entry = self._cache[epic_key]

            # Check if expired
            if datetime.now() > entry['expires_at']:
                print(f"DEBUG DocumentCache: Cache expired for {epic_key}")
                del self._cache[epic_key]
                return None

            print(f"DEBUG DocumentCache: Cache hit for {epic_key}")
            return entry['epic_attachments'], entry['child_attachments']

    def clear(self, epic_key: Optional[str] = None) -> None:
        """
        Clear cache entries.

        Args:
            epic_key: If provided, clear only this epic. Otherwise, clear all.
        """
        with self._lock:
            if epic_key:
                if epic_key in self._cache:
                    del self._cache[epic_key]
                    print(f"DEBUG DocumentCache: Cleared cache for {epic_key}")
            else:
                self._cache.clear()
                print(f"DEBUG DocumentCache: Cleared entire cache")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry['expires_at']
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                print(f"DEBUG DocumentCache: Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_entries = len(self._cache)
            now = datetime.now()
            active_entries = sum(1 for entry in self._cache.values() if now <= entry['expires_at'])

            return {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': total_entries - active_entries,
                'ttl_hours': self._ttl.total_seconds() / 3600
            }


# Global document cache instance
document_cache = DocumentCache(ttl_hours=2)
