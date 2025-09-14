"""
Tests for T6.4: Content-addressed caching for render operations.
"""

import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from generator.renderer.cache import (
    RenderCache,
    CacheKey,
    CacheEntry,
    CachedOperation,
    get_default_cache,
    create_content_hash,
    create_file_hash,
)


class TestCacheKey:
    """Test cache key functionality."""

    def test_cache_key_creation(self):
        """Test creating cache keys with all fields."""
        key = CacheKey(
            content_hash="abc123",
            cache_version="1.0",
            operation_type="scene_render",
            parameters_hash="def456",
        )

        assert key.content_hash == "abc123"
        assert key.cache_version == "1.0"
        assert key.operation_type == "scene_render"
        assert key.parameters_hash == "def456"

    def test_cache_key_string_representation(self):
        """Test cache key string conversion for file naming."""
        key = CacheKey(
            content_hash="abc123",
            cache_version="1.0",
            operation_type="scene_render",
            parameters_hash="def456",
        )

        key_str = key.to_string()
        expected = "scene_render_abc123_def456_1.0"
        assert key_str == expected


class TestRenderCache:
    """Test render cache functionality."""

    def setup_method(self):
        """Setup test cache with temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = RenderCache(
            cache_dir=self.temp_dir / "cache", max_size_gb=1.0, ttl_hours=1.0
        )

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cache_initialization(self):
        """Test cache initializes correctly."""
        assert self.cache.cache_dir.exists()
        assert self.cache.max_size_gb == 1.0
        assert self.cache.ttl_hours == 1.0
        assert self.cache.enabled

    def test_scene_render_key_creation(self):
        """Test creating cache key for scene rendering."""
        scene_content = """
from manim import *
class TestScene(Scene):
    def construct(self):
        self.add(Text("Hello"))
        """

        key = self.cache.create_scene_render_key(
            scene_content=scene_content,
            quality="1080p",
            timeout_s=180,
            additional_params={"fps": 30},
        )

        assert key.operation_type == "scene_render"
        assert key.content_hash  # Should have content hash
        assert key.parameters_hash  # Should have params hash
        assert key.cache_version == "1.0"

    def test_scene_render_key_deterministic(self):
        """Test scene render keys are deterministic for same inputs."""
        scene_content = "from manim import *\nclass TestScene(Scene): pass"

        key1 = self.cache.create_scene_render_key(
            scene_content=scene_content, quality="1080p", timeout_s=180
        )

        key2 = self.cache.create_scene_render_key(
            scene_content=scene_content, quality="1080p", timeout_s=180
        )

        assert key1.to_string() == key2.to_string()

    def test_scene_render_key_changes_with_content(self):
        """Test scene render keys change when content changes."""
        key1 = self.cache.create_scene_render_key(
            scene_content="content1", quality="1080p", timeout_s=180
        )

        key2 = self.cache.create_scene_render_key(
            scene_content="content2", quality="1080p", timeout_s=180
        )

        assert key1.to_string() != key2.to_string()

    def test_scene_render_key_changes_with_quality(self):
        """Test scene render keys change when quality changes."""
        key1 = self.cache.create_scene_render_key(
            scene_content="same content", quality="1080p", timeout_s=180
        )

        key2 = self.cache.create_scene_render_key(
            scene_content="same content", quality="720p", timeout_s=180
        )

        assert key1.to_string() != key2.to_string()

    def test_concat_key_creation(self):
        """Test creating cache key for concatenation."""
        input_hashes = ["hash1", "hash2", "hash3"]
        quality_settings = {"crf": 18, "preset": "medium"}

        key = self.cache.create_concat_key(
            input_file_hashes=input_hashes,
            crossfade_s=0.5,
            quality_settings=quality_settings,
        )

        assert key.operation_type == "concat"
        assert key.content_hash
        assert key.parameters_hash

    def test_thumbnail_key_creation(self):
        """Test creating cache key for thumbnails."""
        video_hash = "video_hash_123"
        specs = [
            {"width": 1280, "height": 720, "time_s": 1.0},
            {"width": 640, "height": 360, "time_s": 5.0},
        ]

        key = self.cache.create_thumbnail_key(
            video_file_hash=video_hash, thumbnail_specs=specs
        )

        assert key.operation_type == "thumbnail"
        assert key.content_hash == video_hash
        assert key.parameters_hash

    def test_cache_miss(self):
        """Test cache miss returns None."""
        key = CacheKey(
            content_hash="missing",
            cache_version="1.0",
            operation_type="scene_render",
            parameters_hash="missing",
        )

        result = self.cache.get(key)
        assert result is None

    def test_cache_put_and_get(self):
        """Test caching and retrieving files."""
        # Create test file
        test_file = self.temp_dir / "test_output.mp4"
        test_file.write_bytes(b"fake video content")

        # Create cache key
        key = self.cache.create_scene_render_key(
            scene_content="test content", quality="1080p", timeout_s=180
        )

        # Cache the file
        metadata = {"duration_s": 10.0, "resolution": (1920, 1080)}
        success = self.cache.put(key, [test_file], metadata)
        assert success

        # Retrieve from cache
        entry = self.cache.get(key)
        assert entry is not None
        assert entry.metadata == metadata
        assert len(entry.file_paths) == 1

        # Check cached file exists and has correct content
        cached_file = Path(entry.file_paths[0])
        assert cached_file.exists()
        assert cached_file.read_bytes() == b"fake video content"

    def test_cache_ttl_expiration(self):
        """Test cache entries expire based on TTL."""
        # Create very short TTL cache
        short_cache = RenderCache(
            cache_dir=self.temp_dir / "short_cache", ttl_hours=0.0001  # ~0.36 seconds
        )

        # Create test file
        test_file = self.temp_dir / "test_ttl.mp4"
        test_file.write_bytes(b"ttl test")

        # Create cache key
        key = short_cache.create_scene_render_key(
            scene_content="ttl test", quality="720p", timeout_s=60
        )

        # Cache the file
        short_cache.put(key, [test_file])

        # Should find it immediately
        entry = short_cache.get(key)
        assert entry is not None

        # Wait for expiration and test again
        time.sleep(0.5)  # Wait longer than TTL (0.36s)

        entry = short_cache.get(key)
        assert entry is None  # Should be expired

    def test_cache_missing_files_cleanup(self):
        """Test cache entries are removed when files are missing."""
        # Create test file
        test_file = self.temp_dir / "test_missing.mp4"
        test_file.write_bytes(b"will be deleted")

        # Create cache key and cache file
        key = self.cache.create_scene_render_key(
            scene_content="missing test", quality="1080p", timeout_s=180
        )

        self.cache.put(key, [test_file])

        # Verify it's cached
        entry = self.cache.get(key)
        assert entry is not None

        # Delete the cached file manually
        cached_path = Path(entry.file_paths[0])
        cached_path.unlink()

        # Should return None and clean up entry
        entry = self.cache.get(key)
        assert entry is None

    def test_cache_stats(self):
        """Test cache statistics collection."""
        # Cache some entries
        for i in range(3):
            test_file = self.temp_dir / f"test_{i}.mp4"
            test_file.write_bytes(f"content {i}".encode())

            key = self.cache.create_scene_render_key(
                scene_content=f"content {i}", quality="1080p", timeout_s=180
            )

            self.cache.put(key, [test_file])

        stats = self.cache.get_cache_stats()

        assert stats["enabled"] is True
        assert stats["total_entries"] == 3
        assert stats["total_files"] == 3
        assert stats["by_operation_type"]["scene_render"] == 3
        assert stats["max_size_gb"] == 1.0

    def test_cache_clear(self):
        """Test clearing cache entries."""
        # Cache some entries
        test_file = self.temp_dir / "test_clear.mp4"
        test_file.write_bytes(b"clear test")

        scene_key = self.cache.create_scene_render_key(
            scene_content="clear test", quality="1080p", timeout_s=180
        )

        concat_key = self.cache.create_concat_key(
            input_file_hashes=["hash1"], crossfade_s=None, quality_settings={}
        )

        self.cache.put(scene_key, [test_file])
        self.cache.put(concat_key, [test_file])

        # Clear only scene renders
        self.cache.clear_cache("scene_render")

        assert self.cache.get(scene_key) is None
        assert self.cache.get(concat_key) is not None

        # Clear all
        self.cache.clear_cache()
        assert self.cache.get(concat_key) is None


class TestCachedOperation:
    """Test cached operation context manager."""

    def setup_method(self):
        """Setup test cache."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = RenderCache(cache_dir=self.temp_dir / "cache")

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cached_operation_miss(self):
        """Test cached operation with cache miss."""
        key = self.cache.create_scene_render_key(
            scene_content="test miss", quality="1080p", timeout_s=180
        )

        with CachedOperation(self.cache, key, "test_operation") as op:
            assert not op.is_cached()
            assert op.get_cached_files() == []
            assert op.get_cached_metadata() == {}

    def test_cached_operation_hit(self):
        """Test cached operation with cache hit."""
        # Create and cache a file first
        test_file = self.temp_dir / "cached_test.mp4"
        test_file.write_bytes(b"cached content")

        key = self.cache.create_scene_render_key(
            scene_content="test hit", quality="1080p", timeout_s=180
        )

        metadata = {"duration_s": 5.0}
        self.cache.put(key, [test_file], metadata)

        # Test cache hit
        with CachedOperation(self.cache, key, "test_operation") as op:
            assert op.is_cached()

            cached_files = op.get_cached_files()
            assert len(cached_files) == 1
            assert cached_files[0].exists()

            cached_metadata = op.get_cached_metadata()
            assert cached_metadata["duration_s"] == 5.0

    def test_cached_operation_cache_result(self):
        """Test caching operation results."""
        key = self.cache.create_scene_render_key(
            scene_content="test cache result", quality="1080p", timeout_s=180
        )

        # Create result file
        result_file = self.temp_dir / "result.mp4"
        result_file.write_bytes(b"operation result")

        with CachedOperation(self.cache, key, "test_operation") as op:
            assert not op.is_cached()

            # Simulate some work
            time.sleep(0.001)

            # Cache the result
            metadata = {"frames": 150}
            success = op.cache_result([result_file], metadata)
            assert success

        # Verify it was cached
        entry = self.cache.get(key)
        assert entry is not None
        assert entry.metadata["operation"] == "test_operation"
        assert "processing_time_s" in entry.metadata
        assert entry.metadata["frames"] == 150


class TestCacheHelpers:
    """Test cache helper functions."""

    def test_create_content_hash(self):
        """Test content hash creation."""
        content = "test content for hashing"
        hash1 = create_content_hash(content)
        hash2 = create_content_hash(content)

        assert hash1 == hash2  # Deterministic
        assert len(hash1) == 64  # SHA256 length

        # Different content should produce different hash
        hash3 = create_content_hash("different content")
        assert hash1 != hash3

    def test_create_file_hash(self):
        """Test file hash creation."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            test_file = temp_dir / "hash_test.txt"
            test_file.write_bytes(b"file content for hashing")

            hash1 = create_file_hash(test_file)
            hash2 = create_file_hash(test_file)

            assert hash1 == hash2  # Deterministic
            assert len(hash1) == 64  # SHA256 length

            # Different file should produce different hash
            test_file2 = temp_dir / "hash_test2.txt"
            test_file2.write_bytes(b"different file content")

            hash3 = create_file_hash(test_file2)
            assert hash1 != hash3

        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_get_default_cache(self):
        """Test default cache instance."""
        cache = get_default_cache()
        assert isinstance(cache, RenderCache)
        assert cache.enabled


class TestCacheIntegration:
    """Test cache integration scenarios."""

    def setup_method(self):
        """Setup integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = RenderCache(cache_dir=self.temp_dir / "cache")

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_scene_render_caching_workflow(self):
        """Test complete scene render caching workflow."""
        scene_content = """
from manim import *
class IntegrationTestScene(Scene):
    def construct(self):
        text = Text("Integration Test")
        self.add(text)
        """

        # First render (cache miss)
        key = self.cache.create_scene_render_key(
            scene_content=scene_content,
            quality="1080p",
            timeout_s=180,
            additional_params={"fps": 30},
        )

        with CachedOperation(self.cache, key, "scene_render") as op:
            assert not op.is_cached()

            # Simulate render output
            output_file = self.temp_dir / "scene_output.mp4"
            output_file.write_bytes(b"rendered scene content")

            # Cache the result
            metadata = {
                "duration_s": 5.0,
                "resolution": (1920, 1080),
                "fps": 30,
                "frames": 150,
            }
            op.cache_result([output_file], metadata)

        # Second render (cache hit)
        with CachedOperation(self.cache, key, "scene_render") as op:
            assert op.is_cached()

            cached_files = op.get_cached_files()
            assert len(cached_files) == 1
            assert cached_files[0].read_bytes() == b"rendered scene content"

            cached_metadata = op.get_cached_metadata()
            assert cached_metadata["duration_s"] == 5.0
            assert cached_metadata["resolution"] == (1920, 1080)

    def test_cache_invalidation_on_content_change(self):
        """Test cache invalidation when scene content changes."""
        original_content = "original scene content"
        modified_content = "modified scene content"

        # Cache original content
        key1 = self.cache.create_scene_render_key(
            scene_content=original_content, quality="1080p", timeout_s=180
        )

        output_file = self.temp_dir / "original_output.mp4"
        output_file.write_bytes(b"original render")

        self.cache.put(key1, [output_file], {"type": "original"})

        # Modified content should have different key
        key2 = self.cache.create_scene_render_key(
            scene_content=modified_content, quality="1080p", timeout_s=180
        )

        assert key1.to_string() != key2.to_string()

        # Cache hit for original, miss for modified
        assert self.cache.get(key1) is not None
        assert self.cache.get(key2) is None
