"""
Simple in-memory cache service for analysis results
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Simple in-memory cache for analysis results"""

    def __init__(self, ttl_minutes: int = 15):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_minutes = ttl_minutes

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if not expired"""
        if key not in self.cache:
            return None

        cached = self.cache[key]
        cached_time = cached.get('timestamp', 0)
        current_time = time.time()

        # Check if cache has expired
        if current_time - cached_time > self.ttl_minutes * 60:
            del self.cache[key]
            logger.info(f"Cache expired for key: {key}")
            return None

        logger.info(f"Cache hit for key: {key}")
        return cached.get('data')

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Set cache data with current timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.info(f"Cached data for key: {key}")

    def clear(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_cache_key(self, symbol: str, analysis_type: str = "full") -> str:
        """Generate cache key for symbol and analysis type"""
        return f"{symbol.upper()}_{analysis_type}_{datetime.now().strftime('%Y%m%d')}"


# Global cache instance
analysis_cache = CacheService(ttl_minutes=15)