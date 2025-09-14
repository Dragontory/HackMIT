"""
T6.4: Content-addressed caching for render operations.

Provides caching for expensive render operations based on content hashes
to avoid re-rendering identical inputs.
"""

import hashlib
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

from .config import CACHE_SETTINGS


@dataclass(frozen=True)
class CacheKey:
    """Content-addressed cache key."""

    content_hash: str
    cache_version: str
    operation_type: str  # "scene_render", "concat", "thumbnail"
    parameters_hash: str

    def to_string(self) -> str:
        """Convert to string representation for file naming."""
        return f"{self.operation_type}_{self.content_hash}_{self.parameters_hash}_{self.cache_version}"


@dataclass(frozen=True)
class CacheEntry:
    """Cache entry metadata."""

    key: CacheKey
    created_at: float
    accessed_at: float
    file_paths: List[str]  # Paths to cached files
    metadata: Dict[str, Any]
    size_bytes: int


class RenderCache:
    """T6.4: Content-addressed cache for render operations."""

    def __init__(
        self, cache_dir: Path = None, max_size_gb: float = None, ttl_hours: float = None
    ):
        """
        Initialize render cache.

        Args:
            cache_dir: Cache directory (defaults to system temp)
            max_size_gb: Maximum cache size in GB
            ttl_hours: Time-to-live in hours
        """
        import tempfile

        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / "manim_render_cache"
        self.max_size_gb = max_size_gb or CACHE_SETTINGS["max_size_gb"]
        self.ttl_hours = ttl_hours or CACHE_SETTINGS["ttl_hours"]
        self.enabled = CACHE_SETTINGS["enabled"]

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_file = self.cache_dir / "cache_metadata.json"
            self._load_metadata()

    def _load_metadata(self):
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    self.entries = {
                        key: CacheEntry(**entry_data)
                        for key, entry_data in data.get("entries", {}).items()
                    }
            except Exception:
                self.entries = {}
        else:
            self.entries = {}

    def _save_metadata(self):
        """Save cache metadata to disk."""
        if not self.enabled:
            return

        try:
            data = {
                "version": CACHE_SETTINGS["cache_key_version"],
                "entries": {key: asdict(entry) for key, entry in self.entries.items()},
            }
            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def create_scene_render_key(
        self,
        scene_content: str,
        quality: str,
        timeout_s: int,
        additional_params: Dict[str, Any] = None,
    ) -> CacheKey:
        """Create cache key for scene rendering operation."""
        # Hash the scene content (Python source code)
        content_hash = self._hash_content(scene_content)

        # Hash rendering parameters
        params = {
            "quality": quality,
            "timeout_s": timeout_s,
            "manim_version": "community",  # Could be detected
            **(additional_params or {}),
        }
        params_hash = self._hash_content(json.dumps(params, sort_keys=True))

        return CacheKey(
            content_hash=content_hash,
            cache_version=CACHE_SETTINGS["cache_key_version"],
            operation_type="scene_render",
            parameters_hash=params_hash,
        )

    def create_concat_key(
        self,
        input_file_hashes: List[str],
        crossfade_s: Optional[float],
        quality_settings: Dict[str, Any],
    ) -> CacheKey:
        """Create cache key for video concatenation operation."""
        # Combine input file hashes
        combined_content = "|".join(sorted(input_file_hashes))
        content_hash = self._hash_content(combined_content)

        # Hash concatenation parameters
        params = {"crossfade_s": crossfade_s, "quality_settings": quality_settings}
        params_hash = self._hash_content(json.dumps(params, sort_keys=True))

        return CacheKey(
            content_hash=content_hash,
            cache_version=CACHE_SETTINGS["cache_key_version"],
            operation_type="concat",
            parameters_hash=params_hash,
        )

    def create_thumbnail_key(
        self, video_file_hash: str, thumbnail_specs: List[Dict[str, Any]]
    ) -> CacheKey:
        """Create cache key for thumbnail generation."""
        content_hash = video_file_hash

        # Hash thumbnail specifications
        params = {"specs": thumbnail_specs}
        params_hash = self._hash_content(json.dumps(params, sort_keys=True))

        return CacheKey(
            content_hash=content_hash,
            cache_version=CACHE_SETTINGS["cache_key_version"],
            operation_type="thumbnail",
            parameters_hash=params_hash,
        )

    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Get cache entry if it exists and is valid."""
        if not self.enabled:
            return None

        key_str = key.to_string()
        entry = self.entries.get(key_str)

        if not entry:
            return None

        # Check TTL
        current_time = time.time()
        age_hours = (current_time - entry.created_at) / 3600
        if age_hours > self.ttl_hours:
            self._remove_entry(key_str)
            return None

        # Check if files still exist
        missing_files = []
        for file_path in entry.file_paths:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            self._remove_entry(key_str)
            return None

        # Update access time
        updated_entry = CacheEntry(
            key=entry.key,
            created_at=entry.created_at,
            accessed_at=current_time,
            file_paths=entry.file_paths,
            metadata=entry.metadata,
            size_bytes=entry.size_bytes,
        )
        self.entries[key_str] = updated_entry
        self._save_metadata()

        return updated_entry

    def put(
        self, key: CacheKey, file_paths: List[Path], metadata: Dict[str, Any] = None
    ) -> bool:
        """Store files in cache."""
        if not self.enabled:
            return False

        try:
            # Calculate total size
            total_size = sum(
                path.stat().st_size for path in file_paths if path.exists()
            )

            # Check if we need to make space
            self._ensure_space(total_size)

            # Copy files to cache directory
            key_str = key.to_string()
            cache_subdir = self.cache_dir / key_str
            cache_subdir.mkdir(parents=True, exist_ok=True)

            cached_file_paths = []
            for file_path in file_paths:
                if file_path.exists():
                    cached_path = cache_subdir / file_path.name
                    shutil.copy2(file_path, cached_path)
                    cached_file_paths.append(str(cached_path))

            # Create cache entry
            current_time = time.time()
            entry = CacheEntry(
                key=key,
                created_at=current_time,
                accessed_at=current_time,
                file_paths=cached_file_paths,
                metadata=metadata or {},
                size_bytes=total_size,
            )

            self.entries[key_str] = entry
            self._save_metadata()
            return True

        except Exception:
            return False

    def _remove_entry(self, key_str: str):
        """Remove cache entry and its files."""
        if key_str not in self.entries:
            return

        entry = self.entries[key_str]

        # Remove files
        cache_subdir = self.cache_dir / key_str
        if cache_subdir.exists():
            try:
                shutil.rmtree(cache_subdir)
            except Exception:
                pass

        # Remove from metadata
        del self.entries[key_str]
        self._save_metadata()

    def _ensure_space(self, needed_bytes: int):
        """Ensure cache has enough space by removing old entries."""
        current_size = sum(entry.size_bytes for entry in self.entries.values())
        max_bytes = int(self.max_size_gb * 1024 * 1024 * 1024)

        if current_size + needed_bytes <= max_bytes:
            return

        # Sort entries by access time (oldest first)
        entries_by_access = sorted(self.entries.items(), key=lambda x: x[1].accessed_at)

        # Remove oldest entries until we have enough space
        for key_str, entry in entries_by_access:
            self._remove_entry(key_str)
            current_size -= entry.size_bytes

            if current_size + needed_bytes <= max_bytes:
                break

    def _hash_content(self, content: str) -> str:
        """Create hash of content using configured algorithm."""
        hasher = hashlib.new(CACHE_SETTINGS["hash_algorithm"])
        hasher.update(content.encode("utf-8"))
        return hasher.hexdigest()

    def hash_file(self, file_path: Path) -> str:
        """Create hash of file contents."""
        hasher = hashlib.new(CACHE_SETTINGS["hash_algorithm"])

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}

        total_size = sum(entry.size_bytes for entry in self.entries.values())
        total_files = sum(len(entry.file_paths) for entry in self.entries.values())

        # Count by operation type
        by_type = {}
        for entry in self.entries.values():
            op_type = entry.key.operation_type
            by_type[op_type] = by_type.get(op_type, 0) + 1

        return {
            "enabled": True,
            "total_entries": len(self.entries),
            "total_size_mb": total_size / (1024 * 1024),
            "total_files": total_files,
            "max_size_gb": self.max_size_gb,
            "ttl_hours": self.ttl_hours,
            "by_operation_type": by_type,
            "cache_dir": str(self.cache_dir),
        }

    def clear_cache(self, operation_type: str = None):
        """Clear cache entries, optionally filtered by operation type."""
        if not self.enabled:
            return

        keys_to_remove = []

        for key_str, entry in self.entries.items():
            if operation_type is None or entry.key.operation_type == operation_type:
                keys_to_remove.append(key_str)

        for key_str in keys_to_remove:
            self._remove_entry(key_str)

    def cleanup_expired(self):
        """Remove expired cache entries."""
        if not self.enabled:
            return

        current_time = time.time()
        expired_keys = []

        for key_str, entry in self.entries.items():
            age_hours = (current_time - entry.created_at) / 3600
            if age_hours > self.ttl_hours:
                expired_keys.append(key_str)

        for key_str in expired_keys:
            self._remove_entry(key_str)

        return len(expired_keys)


def get_default_cache() -> RenderCache:
    """Get default render cache instance."""
    return RenderCache()


def create_content_hash(content: str) -> str:
    """Create content hash using configured algorithm."""
    hasher = hashlib.new(CACHE_SETTINGS["hash_algorithm"])
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def create_file_hash(file_path: Path) -> str:
    """Create hash of file contents."""
    hasher = hashlib.new(CACHE_SETTINGS["hash_algorithm"])

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


class CachedOperation:
    """Context manager for cached operations."""

    def __init__(
        self, cache: RenderCache, cache_key: CacheKey, operation_name: str = "operation"
    ):
        self.cache = cache
        self.cache_key = cache_key
        self.operation_name = operation_name
        self.cached_entry = None
        self.start_time = time.time()

    def __enter__(self):
        """Check for cached result."""
        self.cached_entry = self.cache.get(self.cache_key)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup (no-op for cached operations)."""
        pass

    def is_cached(self) -> bool:
        """Check if operation result is cached."""
        return self.cached_entry is not None

    def get_cached_files(self) -> List[Path]:
        """Get paths to cached files."""
        if not self.cached_entry:
            return []
        return [Path(path) for path in self.cached_entry.file_paths]

    def get_cached_metadata(self) -> Dict[str, Any]:
        """Get cached metadata."""
        if not self.cached_entry:
            return {}
        return self.cached_entry.metadata

    def cache_result(
        self, result_files: List[Path], metadata: Dict[str, Any] = None
    ) -> bool:
        """Cache operation result files."""
        processing_time = time.time() - self.start_time

        # Add processing time to metadata
        full_metadata = metadata or {}
        full_metadata.update(
            {
                "operation": self.operation_name,
                "processing_time_s": processing_time,
                "cached_at": time.time(),
            }
        )

        return self.cache.put(
            key=self.cache_key, file_paths=result_files, metadata=full_metadata
        )
