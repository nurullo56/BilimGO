from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheService:
    """Async Cache Service (In-Memory with TTL, extendable with Redis)."""

    def __init__(self) -> None:
        self._memory_cache: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._memory_cache:
                return None
            value, expires_at = self._memory_cache[key]
            if expires_at is not None and time.time() > expires_at:
                del self._memory_cache[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            expires_at = time.time() + ttl if ttl is not None else None
            self._memory_cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._memory_cache.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._memory_cache.clear()


cache_service = CacheService()
