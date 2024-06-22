import contextlib

import threading
import time

from collections import deque
from dataclasses import dataclass

from typing import Any, Callable, Dict, Optional, Protocol


class _LockType(contextlib.AbstractContextManager, Protocol):
    def acquire(self, blocking: bool = ..., timeout: float = ...) -> bool: ...
    def release(self) -> None: ...


def ensure_lock(lock: _LockType | None) -> _LockType:
    return threading.Lock() if lock is None else lock


@dataclass
class LRUNode:
    key: str

    value: Any
    ttl: float


class LRUCache:
    def __init__(
        self,
        lock: _LockType,
        max_capacity: Optional[int],
        ttl_seconds: Optional[int],
        on_remove: Optional[Callable[[Any], None]],
    ):
        self._lock = lock
        self._max_capacity = max_capacity if max_capacity else 0
        self._ttl_seconds = ttl_seconds if ttl_seconds else 0
        self._on_remove = on_remove
        self._map: Dict[str, LRUNode] = {}
        self._lru: deque[LRUNode] = deque([])

    def _move_to_front(self, entry: LRUNode) -> None:
        self._lru.remove(entry)
        self._lru.append(entry)

    def add(self, key: str, value: Any) -> Optional[Any]:
        with self._lock:
            entry: Optional[LRUNode] = self._map.get(key)
            ttl = int(time.time()) + self._ttl_seconds

            if entry:
                old_value = entry.value
                entry.value = value
                entry.ttl = ttl
                self._move_to_front(entry)

                return old_value

            entry = LRUNode(key, value, ttl)

            self._map[key] = entry
            self._lru.append(entry)

            if self._max_capacity > 0 and len(self._lru) > self._max_capacity:
                popped = self._lru.popleft()

                self._map.pop(popped.key)

                if self._on_remove:
                    self._on_remove(popped.value)

            return None

    def remove(self, key: str) -> None:
        with self._lock:
            entry: Optional[LRUNode] = self._map.get(key)
            if entry:
                self._map.pop(key)
                self._lru.remove(entry)

                if self._on_remove:
                    self._on_remove(entry.value)

    def clear(self) -> None:
        with self._lock:
            if self._on_remove:
                for entry in self._lru:
                    self._on_remove(entry.value)

            self._map.clear()
            self._lru.clear()

    def get(self, key: str, default: Optional[Any]) -> Optional[Any]:
        with self._lock:
            entry: Optional[LRUNode] = self._map.get(key)

            if not entry:
                return default

            if self._ttl_seconds > 0 and entry.ttl < time.time():
                self._map.pop(key)
                self._lru.remove(entry)

                if self._on_remove:
                    self._on_remove(entry.value)

                return default

            entry.ttl = time.time() + self._ttl_seconds
            self._move_to_front(entry)
            return entry.value
