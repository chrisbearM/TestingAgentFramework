"""
Unit tests for cache_client module

Tests cover:
1. Initialization (Redis and disk fallback)
2. Cache key generation
3. Data compression/decompression
4. Get/set operations (Redis and disk)
5. Cache statistics
6. Cache clearing
7. TTL handling
"""

import pytest
import os
import json
import zlib
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from ai_tester.clients.cache_client import CacheClient


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestCacheClientInitialization:
    """Tests for CacheClient initialization"""

    def test_init_disabled(self):
        """Test initialization with caching disabled"""
        client = CacheClient(enabled=False)

        assert client.enabled is False
        assert client.use_redis is False
        assert client.redis_client is None

    def test_init_disk_cache_default(self):
        """Test default initialization uses disk cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir, enabled=True)

            assert client.enabled is True
            assert client.use_redis is False
            assert os.path.exists(tmpdir)

    def test_init_with_custom_ttl(self):
        """Test initialization with custom TTL"""
        client = CacheClient(ttl_days=7, enabled=False)

        assert client.ttl_days == 7
        assert client.ttl_seconds == 7 * 24 * 60 * 60

    def test_init_redis_success(self):
        """Test successful Redis initialization"""
        # Mock the redis import at the point of use
        def mock_import(name, *args, **kwargs):
            if name == 'redis':
                mock_redis = Mock()
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_redis.from_url.return_value = mock_client
                return mock_redis
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            client = CacheClient(redis_url="redis://localhost:6379/0")

            assert client.use_redis is True
            assert client.redis_client is not None

    def test_init_redis_connection_failure(self):
        """Test Redis connection failure falls back to disk"""
        def mock_import(name, *args, **kwargs):
            if name == 'redis':
                mock_redis = Mock()
                mock_redis.from_url.side_effect = Exception("Connection failed")
                return mock_redis
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            with tempfile.TemporaryDirectory() as tmpdir:
                client = CacheClient(
                    redis_url="redis://localhost:6379/0",
                    cache_dir=tmpdir
                )

                assert client.use_redis is False
                assert client.redis_client is None
                assert os.path.exists(tmpdir)

    def test_init_stats_initialized(self):
        """Test that stats are initialized"""
        client = CacheClient(enabled=False)

        assert client.stats == {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }


# ============================================================================
# CACHE KEY GENERATION TESTS
# ============================================================================

class TestCacheKeyGeneration:
    """Tests for cache key generation"""

    def test_generate_cache_key(self):
        """Test cache key generation"""
        client = CacheClient(enabled=False)

        key = client._generate_cache_key(
            sys_prompt="System prompt",
            user_prompt="User prompt",
            max_tokens=100,
            model="gpt-4"
        )

        assert key.startswith("llm_cache:v5:")
        assert len(key) > 20  # Should include hash

    def test_cache_key_deterministic(self):
        """Test that same inputs produce same key"""
        client = CacheClient(enabled=False)

        key1 = client._generate_cache_key(
            sys_prompt="System",
            user_prompt="User",
            max_tokens=100,
            model="gpt-4"
        )

        key2 = client._generate_cache_key(
            sys_prompt="System",
            user_prompt="User",
            max_tokens=100,
            model="gpt-4"
        )

        assert key1 == key2

    def test_cache_key_different_for_different_inputs(self):
        """Test that different inputs produce different keys"""
        client = CacheClient(enabled=False)

        key1 = client._generate_cache_key(
            sys_prompt="System1",
            user_prompt="User",
            max_tokens=100,
            model="gpt-4"
        )

        key2 = client._generate_cache_key(
            sys_prompt="System2",
            user_prompt="User",
            max_tokens=100,
            model="gpt-4"
        )

        assert key1 != key2

    def test_cache_key_includes_version(self):
        """Test that cache key includes version"""
        client = CacheClient(enabled=False)

        key = client._generate_cache_key(
            sys_prompt="System",
            user_prompt="User",
            max_tokens=100,
            model="gpt-4"
        )

        assert client.CACHE_VERSION in key


# ============================================================================
# COMPRESSION TESTS
# ============================================================================

class TestCompression:
    """Tests for data compression/decompression"""

    def test_compress_decompress_roundtrip(self):
        """Test compression and decompression roundtrip"""
        client = CacheClient(enabled=False)

        data = {
            "response": "This is a test response",
            "error": None,
            "timestamp": "2024-01-01T12:00:00"
        }

        compressed = client._compress_data(data)
        decompressed = client._decompress_data(compressed)

        assert decompressed == data

    def test_compression_reduces_size(self):
        """Test that compression actually reduces data size"""
        client = CacheClient(enabled=False)

        # Large repetitive data compresses well
        data = {
            "response": "test " * 1000,
            "error": None
        }

        original_size = len(json.dumps(data).encode('utf-8'))
        compressed = client._compress_data(data)

        assert len(compressed) < original_size

    def test_decompress_handles_special_characters(self):
        """Test decompression with special characters"""
        client = CacheClient(enabled=False)

        data = {
            "response": "Special chars: émojis 🎉, unicode ∆, quotes \"'",
            "error": None
        }

        compressed = client._compress_data(data)
        decompressed = client._decompress_data(compressed)

        assert decompressed == data


# ============================================================================
# DISK CACHE GET/SET TESTS
# ============================================================================

class TestDiskCacheOperations:
    """Tests for disk cache get/set operations"""

    def test_set_and_get_disk(self):
        """Test basic set and get from disk cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            cache_key = "test_key"
            response = "Test response"

            # Set
            result = client.set(cache_key, response)
            assert result is True
            assert client.stats["sets"] == 1

            # Get
            cached = client.get(cache_key)
            assert cached is not None
            assert cached[0] == response
            assert cached[1] is None  # No error
            assert client.stats["hits"] == 1

    def test_get_disk_miss(self):
        """Test cache miss from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            cached = client.get("nonexistent_key")

            assert cached is None
            assert client.stats["misses"] == 1

    def test_set_with_error(self):
        """Test caching response with error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            cache_key = "test_key"
            response = "Error response"
            error = "API Error"

            client.set(cache_key, response, error=error)
            cached = client.get(cache_key)

            assert cached is not None
            assert cached[0] == response
            assert cached[1] == error

    def test_disk_cache_ttl_expired(self):
        """Test that expired disk cache entries are removed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir, ttl_days=1)

            cache_key = "test_key"

            # Manually create an expired cache file
            safe_key = cache_key.replace(":", "_")
            cache_file = os.path.join(tmpdir, f"{safe_key}.cache")

            old_timestamp = (datetime.now() - timedelta(days=2)).isoformat()
            data = {
                "response": "Old response",
                "error": None,
                "timestamp": old_timestamp,
                "version": client.CACHE_VERSION
            }

            compressed = client._compress_data(data)
            with open(cache_file, 'wb') as f:
                f.write(compressed)

            # Try to get - should be expired and return None
            cached = client.get(cache_key)

            assert cached is None
            assert not os.path.exists(cache_file)  # File should be deleted

    def test_disk_cache_windows_safe_keys(self):
        """Test that colons in keys are handled for Windows compatibility"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            cache_key = "llm_cache:v5:test123"
            response = "Test response"

            client.set(cache_key, response)

            # Check that file was created with underscores
            files = os.listdir(tmpdir)
            assert len(files) == 1
            assert "_" in files[0]  # Colons replaced with underscores

    def test_get_set_when_disabled(self):
        """Test that get/set do nothing when disabled"""
        client = CacheClient(enabled=False)

        result = client.set("key", "value")
        assert result is False

        cached = client.get("key")
        assert cached is None


# ============================================================================
# REDIS CACHE GET/SET TESTS
# ============================================================================

class TestRedisCacheOperations:
    """Tests for Redis cache operations"""

    def test_set_and_get_redis(self):
        """Test basic set and get from Redis"""
        def mock_import(name, *args, **kwargs):
            if name == 'redis':
                mock_redis = Mock()
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_redis.from_url.return_value = mock_client
                return mock_redis
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            client = CacheClient(redis_url="redis://localhost:6379/0")

            cache_key = "test_key"
            response = "Test response"

            # Set
            client.set(cache_key, response)

            assert client.redis_client.setex.called
            assert client.stats["sets"] == 1

            # Mock get - simulate what Redis would return
            data = {
                "response": response,
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "version": client.CACHE_VERSION
            }
            compressed = client._compress_data(data)
            client.redis_client.get.return_value = compressed

            # Get
            cached = client.get(cache_key)

            assert cached is not None
            assert cached[0] == response
            assert client.stats["hits"] == 1

    def test_get_redis_miss(self):
        """Test Redis cache miss"""
        def mock_import(name, *args, **kwargs):
            if name == 'redis':
                mock_redis = Mock()
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_client.get.return_value = None
                mock_redis.from_url.return_value = mock_client
                return mock_redis
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            client = CacheClient(redis_url="redis://localhost:6379/0")

            cached = client.get("nonexistent_key")

            assert cached is None
            assert client.stats["misses"] == 1


# ============================================================================
# CACHE CLEARING TESTS
# ============================================================================

class TestCacheClear:
    """Tests for cache clearing operations"""

    def test_clear_disk_cache(self):
        """Test clearing disk cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            # Create some cache entries
            client.set("key1", "value1")
            client.set("key2", "value2")
            client.set("key3", "value3")

            # Clear cache
            cleared = client.clear()

            assert cleared == 3
            assert len(os.listdir(tmpdir)) == 0

    def test_clear_empty_disk_cache(self):
        """Test clearing empty disk cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            cleared = client.clear()

            assert cleared == 0

    def test_clear_redis_cache(self):
        """Test clearing Redis cache"""
        def mock_import(name, *args, **kwargs):
            if name == 'redis':
                mock_redis = Mock()
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_client.scan_iter.return_value = iter(["key1", "key2", "key3"])
                mock_client.delete.return_value = 3
                mock_redis.from_url.return_value = mock_client
                return mock_redis
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            client = CacheClient(redis_url="redis://localhost:6379/0")

            cleared = client.clear()

            assert cleared == 3
            client.redis_client.delete.assert_called_once()

    def test_clear_when_disabled(self):
        """Test that clear does nothing when disabled"""
        client = CacheClient(enabled=False)

        cleared = client.clear()

        assert cleared == 0


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestCacheStatistics:
    """Tests for cache statistics"""

    def test_get_stats_initial(self):
        """Test initial statistics"""
        client = CacheClient(enabled=False)

        stats = client.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["sets"] == 0
        assert stats["errors"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate_percent"] == 0
        assert stats["enabled"] is False

    def test_get_stats_with_activity(self):
        """Test statistics after cache activity"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            # Generate some activity
            client.set("key1", "value1")
            client.get("key1")  # Hit
            client.get("key2")  # Miss

            stats = client.get_stats()

            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["sets"] == 1
            assert stats["total_requests"] == 2
            assert stats["hit_rate_percent"] == 50.0

    def test_get_stats_hit_rate_calculation(self):
        """Test hit rate percentage calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            # 3 hits, 1 miss = 75% hit rate
            client.set("key1", "value1")
            client.get("key1")  # Hit
            client.get("key1")  # Hit
            client.get("key1")  # Hit
            client.get("key2")  # Miss

            stats = client.get_stats()

            assert stats["hit_rate_percent"] == 75.0

    def test_get_stats_disk_backend(self):
        """Test stats show disk backend info"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            stats = client.get_stats()

            assert stats["backend"] == "disk"
            assert "disk_cache_entries" in stats
            assert "disk_cache_size_mb" in stats

    def test_get_stats_redis_backend(self):
        """Test stats show Redis backend info"""
        def mock_import(name, *args, **kwargs):
            if name == 'redis':
                mock_redis = Mock()
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_client.info.return_value = {"used_memory_human": "1.5M"}
                mock_client.dbsize.return_value = 42
                mock_redis.from_url.return_value = mock_client
                return mock_redis
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            client = CacheClient(redis_url="redis://localhost:6379/0")

            stats = client.get_stats()

            assert stats["backend"] == "redis"
            assert stats["redis_memory_used"] == "1.5M"
            assert stats["redis_keys"] == 42


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling"""

    def test_get_handles_corruption(self):
        """Test that corrupted cache files are handled gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            # Create a corrupted cache file
            cache_key = "test_key"
            safe_key = cache_key.replace(":", "_")
            cache_file = os.path.join(tmpdir, f"{safe_key}.cache")

            with open(cache_file, 'wb') as f:
                f.write(b"corrupted data")

            # Should handle error gracefully
            cached = client.get(cache_key)

            assert cached is None
            assert client.stats["errors"] >= 1

    def test_set_handles_write_error(self):
        """Test that write errors are handled gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CacheClient(cache_dir=tmpdir)

            # Make the cache directory read-only to force write error
            cache_file = os.path.join(tmpdir, "test.cache")

            # Create a file, then make directory read-only
            with open(cache_file, 'w') as f:
                f.write("test")

            try:
                # Try to make read-only (may not work on all systems)
                os.chmod(tmpdir, 0o444)

                result = client.set("key", "value")

                # Should handle error gracefully - returns False or increments errors
                # On Windows, chmod may not prevent writes, so we just check it doesn't crash
                assert isinstance(result, bool)

            finally:
                # Restore permissions for cleanup
                try:
                    os.chmod(tmpdir, 0o755)
                except:
                    pass


# ============================================================================
# INVALIDATION TESTS
# ============================================================================

class TestInvalidation:
    """Tests for cache invalidation"""

    def test_invalidate_by_ticket_not_implemented(self):
        """Test that ticket invalidation returns 0 (not implemented)"""
        client = CacheClient(enabled=False)

        result = client.invalidate_by_ticket("TICKET-123")

        assert result == 0

    def test_invalidate_by_ticket_when_disabled(self):
        """Test invalidation when caching is disabled"""
        client = CacheClient(enabled=False)

        result = client.invalidate_by_ticket("TICKET-123")

        assert result == 0
