"""
Caching utilities for the PharmaMiku backend.
Provides LRU cache for repeated prompts and responses.
"""

from functools import lru_cache
from typing import Optional, Dict, Any
import hashlib
import json
import time

# In-memory cache with TTL
_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = 3600  # 1 hour default TTL


def _generate_cache_key(message: str, context: Optional[Dict] = None) -> str:
    """Generate a cache key from message and optional context."""
    cache_data = {"message": message}
    if context:
        cache_data.update(context)
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.sha256(cache_str.encode()).hexdigest()


def get_cached_response(message: str, context: Optional[Dict] = None) -> Optional[Any]:
    """
    Retrieve a cached response if available and not expired.
    
    Args:
        message: User message
        context: Optional context dict (e.g., classification, safety assessment)
    
    Returns:
        Cached response if found and valid, None otherwise
    """
    cache_key = _generate_cache_key(message, context)
    
    if cache_key in _cache:
        entry = _cache[cache_key]
        # Check if entry is expired
        if time.time() - entry["timestamp"] < _cache_ttl:
            return entry["data"]
        else:
            # Remove expired entry
            del _cache[cache_key]
    
    return None


def set_cached_response(message: str, response: Any, context: Optional[Dict] = None, ttl: Optional[int] = None):
    """
    Cache a response for future requests.
    
    Args:
        message: User message
        response: Response to cache
        context: Optional context dict
        ttl: Time to live in seconds (defaults to global _cache_ttl)
    """
    cache_key = _generate_cache_key(message, context)
    _cache[cache_key] = {
        "data": response,
        "timestamp": time.time(),
        "ttl": ttl or _cache_ttl
    }
    
    # Limit cache size (keep most recent 1000 entries)
    if len(_cache) > 1000:
        # Remove oldest entries
        sorted_entries = sorted(_cache.items(), key=lambda x: x[1]["timestamp"])
        for key, _ in sorted_entries[:-1000]:
            del _cache[key]


def clear_cache():
    """Clear all cached entries."""
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "size": len(_cache),
        "max_size": 1000,
        "ttl_seconds": _cache_ttl
    }

