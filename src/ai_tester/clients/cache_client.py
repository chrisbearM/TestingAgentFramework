"""
LLM Response Caching Client with Redis support and disk fallback.

Provides transparent caching layer for LLM API calls to reduce costs.
Uses Redis for production/multi-user scenarios, falls back to disk cache.
"""

import hashlib
import json
import os
import zlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CacheClient:
    """
    Caching client for LLM responses with Redis primary and disk fallback.

    Features:
    - Automatic compression for space efficiency
    - TTL support (default 30 days)
    - Cache versioning for prompt changes
    - Fallback to disk if Redis unavailable
    - Cache statistics tracking
    """

    CACHE_VERSION = "v1"  # Increment when prompts change significantly

    def __init__(
        self,
        redis_url: Optional[str] = None,
        cache_dir: str = ".cache/llm",
        ttl_days: int = 30,
        enabled: bool = True
    ):
        """
        Initialize cache client.

        Args:
            redis_url: Redis connection string (redis://localhost:6379/0)
            cache_dir: Directory for disk cache fallback
            ttl_days: Time-to-live in days for cached entries
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.ttl_days = ttl_days
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        self.cache_dir = cache_dir
        self.redis_client = None
        self.use_redis = False

        # Stats tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }

        if not enabled:
            logger.info("LLM caching is disabled")
            return

        # Try to initialize Redis
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,  # We handle binary data
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info(f"LLM cache initialized with Redis: {redis_url}")
            except ImportError:
                logger.warning("redis package not installed. Install with: pip install redis")
                logger.info("Falling back to disk cache")
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                logger.info("Falling back to disk cache")
                self.redis_client = None

        # Initialize disk cache fallback
        if not self.use_redis:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"LLM cache initialized with disk storage: {cache_dir}")

    def _generate_cache_key(
        self,
        sys_prompt: str,
        user_prompt: str,
        max_tokens: int,
        model: str
    ) -> str:
        """
        Generate deterministic cache key from LLM call parameters.

        Includes cache version to invalidate old entries when prompts change.
        """
        # Combine all deterministic parameters
        content = f"{self.CACHE_VERSION}|{model}|{max_tokens}|{sys_prompt}|{user_prompt}"

        # Generate SHA256 hash
        key_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        return f"llm_cache:{self.CACHE_VERSION}:{key_hash}"

    def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """Compress data for storage efficiency."""
        json_str = json.dumps(data)
        return zlib.compress(json_str.encode('utf-8'), level=6)

    def _decompress_data(self, compressed: bytes) -> Dict[str, Any]:
        """Decompress stored data."""
        json_str = zlib.decompress(compressed).decode('utf-8')
        return json.loads(json_str)

    def get(self, cache_key: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Retrieve cached LLM response.

        Returns:
            Tuple of (response_text, error) if found, None if not cached
        """
        if not self.enabled:
            return None

        try:
            if self.use_redis:
                return self._get_redis(cache_key)
            else:
                return self._get_disk(cache_key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats["errors"] += 1
            return None

    def _get_redis(self, cache_key: str) -> Optional[Tuple[str, Optional[str]]]:
        """Get from Redis cache."""
        try:
            compressed = self.redis_client.get(cache_key)
            if compressed:
                data = self._decompress_data(compressed)
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT (Redis): {cache_key[:16]}...")
                return (data["response"], data.get("error"))
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache MISS (Redis): {cache_key[:16]}...")
                return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats["errors"] += 1
            return None

    def _get_disk(self, cache_key: str) -> Optional[Tuple[str, Optional[str]]]:
        """Get from disk cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.cache")

        if not os.path.exists(cache_file):
            self.stats["misses"] += 1
            logger.debug(f"Cache MISS (Disk): {cache_key[:16]}...")
            return None

        try:
            with open(cache_file, 'rb') as f:
                compressed = f.read()

            data = self._decompress_data(compressed)

            # Check TTL
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time > timedelta(days=self.ttl_days):
                logger.debug(f"Cache EXPIRED (Disk): {cache_key[:16]}...")
                os.remove(cache_file)
                self.stats["misses"] += 1
                return None

            self.stats["hits"] += 1
            logger.debug(f"Cache HIT (Disk): {cache_key[:16]}...")
            return (data["response"], data.get("error"))

        except Exception as e:
            logger.error(f"Disk cache read error: {e}")
            self.stats["errors"] += 1
            return None

    def set(
        self,
        cache_key: str,
        response: str,
        error: Optional[str] = None
    ) -> bool:
        """
        Store LLM response in cache.

        Args:
            cache_key: Generated cache key
            response: LLM response text
            error: Error message if any

        Returns:
            True if successfully cached
        """
        if not self.enabled:
            return False

        try:
            data = {
                "response": response,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "version": self.CACHE_VERSION
            }

            if self.use_redis:
                return self._set_redis(cache_key, data)
            else:
                return self._set_disk(cache_key, data)

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.stats["errors"] += 1
            return False

    def _set_redis(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Store in Redis cache."""
        try:
            compressed = self._compress_data(data)
            self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                compressed
            )
            self.stats["sets"] += 1
            logger.debug(f"Cache SET (Redis): {cache_key[:16]}... ({len(compressed)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self.stats["errors"] += 1
            return False

    def _set_disk(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Store in disk cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.cache")

        try:
            compressed = self._compress_data(data)
            with open(cache_file, 'wb') as f:
                f.write(compressed)

            self.stats["sets"] += 1
            logger.debug(f"Cache SET (Disk): {cache_key[:16]}... ({len(compressed)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Disk cache write error: {e}")
            self.stats["errors"] += 1
            return False

    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (Redis only)

        Returns:
            Number of entries cleared
        """
        if not self.enabled:
            return 0

        try:
            if self.use_redis:
                return self._clear_redis(pattern)
            else:
                return self._clear_disk()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def _clear_redis(self, pattern: Optional[str] = None) -> int:
        """Clear Redis cache."""
        try:
            pattern = pattern or "llm_cache:*"
            keys = list(self.redis_client.scan_iter(match=pattern, count=100))
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} Redis cache entries")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    def _clear_disk(self) -> int:
        """Clear disk cache."""
        try:
            count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
                    count += 1
            logger.info(f"Cleared {count} disk cache entries")
            return count
        except Exception as e:
            logger.error(f"Disk cache clear error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit rate, etc.
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        stats = {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "backend": "redis" if self.use_redis else "disk",
            "enabled": self.enabled,
            "ttl_days": self.ttl_days
        }

        # Add Redis-specific stats
        if self.use_redis:
            try:
                info = self.redis_client.info('memory')
                stats["redis_memory_used"] = info.get('used_memory_human', 'N/A')
                stats["redis_keys"] = self.redis_client.dbsize()
            except Exception:
                pass
        else:
            # Add disk cache stats
            try:
                cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.cache')]
                total_size = sum(
                    os.path.getsize(os.path.join(self.cache_dir, f))
                    for f in cache_files
                )
                stats["disk_cache_entries"] = len(cache_files)
                stats["disk_cache_size_mb"] = round(total_size / (1024 * 1024), 2)
            except Exception:
                pass

        return stats

    def invalidate_by_ticket(self, ticket_key: str) -> int:
        """
        Invalidate cache entries for a specific ticket.

        Useful when ticket is updated in Jira.
        """
        if not self.enabled:
            return 0

        # For now, we can't easily match by ticket content in the hash
        # This would require storing metadata alongside cache entries
        # TODO: Implement metadata index for granular invalidation
        logger.warning(f"Ticket-level invalidation not yet implemented for {ticket_key}")
        return 0
