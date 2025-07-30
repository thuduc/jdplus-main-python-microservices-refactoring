"""Plot caching system."""

import os
import time
import asyncio
from typing import Optional, Dict
from pathlib import Path
import hashlib
import json


class PlotCache:
    """In-memory plot cache with file backing."""
    
    def __init__(self, cache_dir: str, max_size: int = 100, ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    def _generate_key(self, plot_type: str, params: dict) -> str:
        """Generate cache key from plot type and parameters."""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        content = f"{plot_type}:{sorted_params}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get(self, plot_type: str, params: dict) -> Optional[str]:
        """Get cached plot path."""
        key = self._generate_key(plot_type, params)
        
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # Check if expired
                if time.time() - entry['timestamp'] < self.ttl:
                    # Check if file still exists
                    if os.path.exists(entry['path']):
                        return entry['path']
                # Remove expired entry
                del self._cache[key]
        
        return None
    
    async def set(self, plot_type: str, params: dict, path: str):
        """Cache plot path."""
        key = self._generate_key(plot_type, params)
        
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k]['timestamp'])
                del self._cache[oldest_key]
            
            self._cache[key] = {
                'path': path,
                'timestamp': time.time()
            }
    
    async def clear(self):
        """Clear cache."""
        async with self._lock:
            self._cache.clear()
    
    def generate_plot_id(self) -> str:
        """Generate unique plot ID."""
        return hashlib.md5(f"{time.time()}".encode()).hexdigest()


# Global cache instance
plot_cache = PlotCache(
    cache_dir=os.getenv("PLOT_CACHE_DIR", "/tmp/plots"),
    max_size=int(os.getenv("MAX_CACHE_SIZE", "100")),
    ttl=int(os.getenv("PLOT_CACHE_TTL", "3600"))
)