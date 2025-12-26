"""
File-based caching system for WorldInsights.

Provides simple file-based caching to reduce API calls and improve performance.
No external dependencies (Redis, etc.) required - works on any infrastructure.

Features:
- TTL-based expiration
- Automatic cleanup of old cache files
- Size limits to prevent disk overflow
- Thread-safe operations
"""
import json
import os
import time
import hashlib
from typing import Any, Optional, Tuple
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileCache:
    """
    Simple file-based cache with TTL support.
    
    Example usage:
        >>> cache = FileCache(cache_dir='/data/cache', max_size_mb=500)
        >>> cache.set('my_key', {'data': 'value'}, ttl=3600)
        >>> data = cache.get('my_key')
    """
    
    def __init__(self, cache_dir: str = None, max_size_mb: int = 500):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory to store cache files (default: /data/cache)
            max_size_mb: Maximum cache size in MB (default: 500)
        """
        if cache_dir is None:
            # Default to data/cache in project root
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / 'data' / 'cache'
        
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileCache initialized at {self.cache_dir} (max size: {max_size_mb}MB)")
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss: {key}")
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if expired
            if cache_data.get('expires_at', 0) < time.time():
                logger.debug(f"Cache expired: {key}")
                cache_path.unlink()  # Delete expired file
                return None
            
            logger.debug(f"Cache hit: {key}")
            return cache_data.get('value')
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cache for {key}: {str(e)}")
            # Delete corrupted cache file
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl,
                'key': key  # Store original key for debugging
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            logger.debug(f"Cached: {key} (TTL: {ttl}s)")
            
            # Check cache size and cleanup if needed
            self._cleanup_if_needed()
            
            return True
            
        except (TypeError, IOError) as e:
            logger.error(f"Failed to cache {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache: {key}")
            return True
        
        return False
    
    def clear(self) -> int:
        """
        Clear all cache files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()
            count += 1
        
        logger.info(f"Cleared {count} cache files")
        return count
    
    def get_cache_size(self) -> int:
        """
        Get total size of cache in bytes.
        
        Returns:
            Total cache size in bytes
        """
        total_size = 0
        for cache_file in self.cache_dir.glob('*.json'):
            total_size += cache_file.stat().st_size
        
        return total_size
    
    def _cleanup_if_needed(self):
        """
        Clean up old cache files if size limit exceeded.
        Removes oldest files first.
        """
        current_size = self.get_cache_size()
        
        if current_size <= self.max_size_bytes:
            return
        
        logger.info(f"Cache size ({current_size / 1024 / 1024:.1f}MB) exceeds limit, cleaning up...")
        
        # Get all cache files sorted by modification time (oldest first)
        cache_files = sorted(
            self.cache_dir.glob('*.json'),
            key=lambda p: p.stat().st_mtime
        )
        
        # Delete oldest files until under limit
        for cache_file in cache_files:
            if current_size <= self.max_size_bytes * 0.8:  # Keep 20% buffer
                break
            
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            current_size -= file_size
            logger.debug(f"Deleted old cache file: {cache_file.name}")
        
        logger.info(f"Cache cleanup complete. New size: {current_size / 1024 / 1024:.1f}MB")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                if cache_data.get('expires_at', 0) < current_time:
                    cache_file.unlink()
                    count += 1
                    
            except (json.JSONDecodeError, IOError):
                # Delete corrupted files
                cache_file.unlink()
                count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired cache files")
        
        return count


# Global cache instance
_cache_instance = None


def get_cache() -> FileCache:
    """
    Get global cache instance (singleton pattern).
    
    Returns:
        FileCache instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = FileCache()
    
    return _cache_instance
