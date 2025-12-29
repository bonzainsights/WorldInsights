
"""
File-based caching system for WorldInsights Backend.
"""
import json
import os
import time
import hashlib
from typing import Any, Optional
from pathlib import Path
from src.core.logging import get_logger

logger = get_logger(__name__)

class FileCache:
    def __init__(self, cache_dir: str = None, max_size_mb: int = 500):
        if cache_dir is None:
            # Default to data/cache relative to backend root 
            # (Assuming run from backend dir -> ../data/cache or backend/data/cache?)
            # Let's use the shared data folder: ../data/cache
            # Adjust based on project structure
            # __file__ is src/core/cache.py
            # parent.parent.parent is 'backend'
            # parent.parent.parent.parent is 'WorldInsights'
            # We want 'WorldInsights/data/cache'
            project_root = Path(__file__).parent.parent.parent.parent
            cache_dir = project_root / 'data' / 'cache'
        
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileCache initialized at {self.cache_dir}")
    
    def _get_cache_path(self, key: str) -> Path:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists(): return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            if cache_data.get('expires_at', 0) < time.time():
                cache_path.unlink()
                return None
            
            return cache_data.get('value')
        except:
            return None
            
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        cache_path = self._get_cache_path(key)
        try:
            cache_data = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl,
                'key': key
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            return True
        except:
            return False

_cache_instance = None

def get_cache() -> FileCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = FileCache()
    return _cache_instance
