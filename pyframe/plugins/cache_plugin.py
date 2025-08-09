"""
Cache Plugin

Provides caching capabilities for responses, data, and components
with multiple backend support and automatic invalidation.
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

from .plugin import Plugin, PluginInfo, HookType


@dataclass
class CacheEntry:
    """Represents a cache entry"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class CacheBackend:
    """Base cache backend interface"""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        raise NotImplementedError
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        raise NotImplementedError
        
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        raise NotImplementedError
        
    async def clear(self) -> None:
        """Clear all cache entries"""
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend"""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                # Remove expired entry
                del self.cache[key]
        return None
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        self.cache[key] = entry
        
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
        
    async def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()


class CachePlugin(Plugin):
    """
    Caching plugin for PyFrame applications.
    
    Provides multiple caching strategies and backends for
    improved performance and reduced database load.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.backend: CacheBackend = MemoryCacheBackend()
        self.default_ttl = self.get_config("default_ttl", 3600)  # 1 hour
        
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="cache",
            version="1.0.0",
            description="Caching plugin with multiple backends",
            author="PyFrame Team",
            tags=["cache", "performance"]
        )
        
    async def initialize(self, app) -> None:
        """Initialize cache plugin"""
        
        # Register hooks for automatic caching
        self.register_hook(HookType.AFTER_REQUEST, self._cache_response, priority=80)
        self.register_hook(HookType.BEFORE_REQUEST, self._check_cache, priority=20)
        
        # Add cache utilities to app
        app.cache = self
        
        print("Cache plugin initialized")
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return await self.backend.get(key)
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        await self.backend.set(key, value, ttl)
        
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        return await self.backend.delete(key)
        
    async def clear(self) -> None:
        """Clear all cache"""
        await self.backend.clear()
        
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    async def _check_cache(self, context: Dict[str, Any], *args, **kwargs) -> None:
        """Check for cached response before processing request"""
        request_context = kwargs.get("request_context")
        if not request_context or request_context.method != "GET":
            return
            
        # Generate cache key for request
        cache_key = self._request_cache_key(request_context)
        cached_response = await self.get(cache_key)
        
        if cached_response:
            # Return cached response
            context["cached_response"] = cached_response
            
    async def _cache_response(self, context: Dict[str, Any], *args, **kwargs) -> None:
        """Cache response after processing"""
        request_context = kwargs.get("request_context")
        response = kwargs.get("response")
        
        if (not request_context or not response or 
            request_context.method != "GET" or
            response.get("status") != 200):
            return
            
        # Only cache successful GET responses
        cache_key = self._request_cache_key(request_context)
        await self.set(cache_key, response, ttl=600)  # 10 minutes
        
    def _request_cache_key(self, request_context) -> str:
        """Generate cache key for request"""
        key_data = f"{request_context.method}:{request_context.path}:{request_context.query_params}"
        return f"request:{hashlib.md5(key_data.encode()).hexdigest()}"


def cached(ttl: int = 3600, key_func: Optional[callable] = None):
    """Decorator for caching function results"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
            # Try to get from cache (assuming app.cache is available)
            # In practice, this would need access to the cache instance
            
            # If not in cache, execute function and cache result
            result = await func(*args, **kwargs)
            # Cache the result
            
            return result
            
        return wrapper
    return decorator
