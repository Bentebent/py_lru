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
        # Perform init
        self._lock = lock
        self._max_capacity = max_capacity
        self._ttl_seconds = ttl_seconds
        self._on_remove = on_remove
        self._map: Dict[str, Any] = {}
        self._lru: list[Any] = list([])

    def pop(self, entry) -> None:
        # TODO: Fix this
        self._lru.remove(entry)
        self._lru.append(entry)

    def add(self, key: str, value) -> Any:
        with self._lock:
            e: Optional[LRUNode] = self._map.get(key)
            d = int(time.time()) + self._ttl_seconds

            if e:
                o = e.value
                e.value = value
                e.ttl = d
                self.pop(e)

                return o

            e = LRUNode(key, value, d)

            self._map[key] = e
            self._lru.append(e)

            if self._max_capacity > 0 and len(self._lru) > self._max_capacity:
                popped = self._lru.popleft()

                self._map.pop(popped.key)

                if self._on_remove:
                    self._on_remove(popped.value)

            return None

    def remove(self, key: str):
        # Do remove
        entry: Optional[LRUNode] = self._map.get(key)
        if entry:
            self._map.pop(key)
            self._lru.remove(entry)

            if self._on_remove:
                self._on_remove(entry.value)

    def clear(self) -> None:
        self._map.clear()
        self._lru.clear()

    def get_the_entry(self, key: str, default: Optional[Any]) -> Optional[Any]:
        with self._lock:
            entry: Optional[LRUNode] = self._map.get(key)

            if self._ttl_seconds > 0 and entry.ttl < time.time():
                self._map.pop(key)
                self._lru.remove(entry)

                if self._on_remove:
                    self._on_remove(entry.value)

                return default

            entry.ttl = time.time() + self._ttl_seconds
            self.pop(entry)
            return entry.value
