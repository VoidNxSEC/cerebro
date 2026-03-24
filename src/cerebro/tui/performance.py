"""
Performance utilities for TUI optimization.

Includes caching, lazy loading, and batch processing utilities.
"""

from typing import Any, Callable, Optional
from functools import lru_cache, wraps
from collections import deque
import time


class Cache:
    """Simple time-based cache for expensive operations."""

    def __init__(self, ttl: int = 60):
        """
        Initialize cache.

        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        self._cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                # Expired, remove
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set cache value.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def invalidate(self, key: str) -> None:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]


def cached(ttl: int = 60):
    """
    Decorator for caching async function results.

    Args:
        ttl: Time to live in seconds

    Example:
        @cached(ttl=30)
        async def get_projects():
            # expensive operation
            return projects
    """
    cache = Cache(ttl=ttl)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        # Expose cache for manual invalidation
        wrapper.cache = cache
        return wrapper

    return decorator


class RingBuffer:
    """
    Memory-efficient ring buffer for logs.

    Uses deque with maxlen for automatic memory management.
    """

    def __init__(self, maxlen: int = 1000):
        """
        Initialize ring buffer.

        Args:
            maxlen: Maximum number of items to store
        """
        self.buffer = deque(maxlen=maxlen)
        self.maxlen = maxlen

    def append(self, item: Any) -> None:
        """
        Append item to buffer.

        Automatically removes oldest item if buffer is full.

        Args:
            item: Item to append
        """
        self.buffer.append(item)

    def extend(self, items: list[Any]) -> None:
        """
        Extend buffer with multiple items.

        Args:
            items: Items to append
        """
        self.buffer.extend(items)

    def get_recent(self, n: int = 100) -> list[Any]:
        """
        Get N most recent items.

        Args:
            n: Number of items to retrieve

        Returns:
            List of recent items
        """
        if n >= len(self.buffer):
            return list(self.buffer)
        return list(self.buffer)[-n:]

    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()

    def __len__(self) -> int:
        """Get buffer length."""
        return len(self.buffer)

    def __iter__(self):
        """Iterate over buffer."""
        return iter(self.buffer)


class BatchProcessor:
    """
    Batch processor for rendering large datasets efficiently.
    """

    @staticmethod
    def paginate(data: list[Any], page_size: int = 100, page: int = 0) -> list[Any]:
        """
        Paginate data.

        Args:
            data: Data to paginate
            page_size: Items per page
            page: Page number (0-indexed)

        Returns:
            Page of data
        """
        start = page * page_size
        end = start + page_size
        return data[start:end]

    @staticmethod
    def chunk(data: list[Any], chunk_size: int = 50) -> list[list[Any]]:
        """
        Split data into chunks.

        Args:
            data: Data to chunk
            chunk_size: Size of each chunk

        Returns:
            List of chunks
        """
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i + chunk_size])
        return chunks

    @staticmethod
    async def process_in_batches(
        data: list[Any],
        processor: Callable,
        batch_size: int = 50,
        delay: float = 0.01
    ) -> list[Any]:
        """
        Process data in batches with delay between batches.

        Args:
            data: Data to process
            processor: Processing function
            batch_size: Items per batch
            delay: Delay between batches in seconds

        Returns:
            Processed results
        """
        import asyncio
        results = []

        chunks = BatchProcessor.chunk(data, batch_size)
        for chunk in chunks:
            # Process chunk
            if asyncio.iscoroutinefunction(processor):
                chunk_results = await processor(chunk)
            else:
                chunk_results = processor(chunk)

            results.extend(chunk_results)

            # Small delay to prevent UI freezing
            await asyncio.sleep(delay)

        return results


class LazyLoader:
    """
    Lazy loader for expensive imports.
    """

    def __init__(self):
        """Initialize lazy loader."""
        self._modules = {}

    def load(self, module_name: str, attribute: Optional[str] = None) -> Any:
        """
        Lazily load module or module attribute.

        Args:
            module_name: Name of module to import
            attribute: Specific attribute to import from module

        Returns:
            Module or module attribute
        """
        cache_key = f"{module_name}:{attribute}"

        if cache_key not in self._modules:
            # Import module
            module = __import__(module_name, fromlist=[attribute] if attribute else [])

            # Get attribute if specified
            if attribute:
                self._modules[cache_key] = getattr(module, attribute)
            else:
                self._modules[cache_key] = module

        return self._modules[cache_key]


# Global instances
_cache = Cache()
_ring_buffer = RingBuffer()
_batch_processor = BatchProcessor()
_lazy_loader = LazyLoader()


# Convenience functions
def get_cache() -> Cache:
    """Get global cache instance."""
    return _cache


def get_ring_buffer() -> RingBuffer:
    """Get global ring buffer instance."""
    return _ring_buffer


def get_batch_processor() -> BatchProcessor:
    """Get global batch processor instance."""
    return _batch_processor


def get_lazy_loader() -> LazyLoader:
    """Get global lazy loader instance."""
    return _lazy_loader
