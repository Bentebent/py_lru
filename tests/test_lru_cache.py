import threading
import time
from typing import Any, List
import multiprocessing
import pytest

from py_lru import LRUCache


@pytest.fixture
def removal_log() -> List[Any]:
    return []


@pytest.fixture
def cache_with_removal_log(removal_log: List[Any]) -> LRUCache:
    def on_remove(value: Any) -> None:
        removal_log.append(value)

    return LRUCache(lock=threading.Lock(), max_capacity=2, ttl_seconds=0, on_remove=on_remove)


def test_add_and_get() -> None:
    cache = LRUCache(lock=threading.Lock(), max_capacity=2, ttl_seconds=0, on_remove=None)
    assert cache.add("key1", "value1") is None
    assert cache.get("key1", None) == "value1"


def test_overwrite_value() -> None:
    cache = LRUCache(lock=threading.Lock(), max_capacity=2, ttl_seconds=0, on_remove=None)
    assert cache.add("key1", "value1") is None
    assert cache.add("key1", "value2") == "value1"
    assert cache.get("key1", None) == "value2"


def test_capacity_eviction(cache_with_removal_log: LRUCache, removal_log: List[Any]) -> None:
    cache = cache_with_removal_log
    cache.add("key1", "value1")
    cache.add("key2", "value2")
    assert cache.add("key3", "value3") is None
    assert cache.get("key1", None) is None
    assert removal_log == ["value1"]


def test_ttl_eviction(cache_with_removal_log: LRUCache, removal_log: List[Any]) -> None:
    cache = LRUCache(lock=threading.Lock(), max_capacity=2, ttl_seconds=1, on_remove=lambda x: removal_log.append(x))
    cache.add("key1", "value1")
    time.sleep(2)
    assert cache.get("key1", None) is None
    assert removal_log == ["value1"]


def test_remove(cache_with_removal_log: LRUCache, removal_log: List[Any]) -> None:
    cache = cache_with_removal_log
    cache.add("key1", "value1")
    cache.remove("key1")
    assert cache.get("key1", None) is None
    assert removal_log == ["value1"]


def test_clear(cache_with_removal_log: LRUCache, removal_log: List[Any]) -> None:
    cache = cache_with_removal_log
    cache.add("key1", "value1")
    cache.add("key2", "value2")
    cache.clear()
    assert cache.get("key1", None) is None
    assert cache.get("key2", None) is None
    assert removal_log == ["value1", "value2"]


def test_lru_order() -> None:
    cache = LRUCache(lock=threading.Lock(), max_capacity=2, ttl_seconds=0, on_remove=None)
    cache.add("key1", "value1")
    cache.add("key2", "value2")
    cache.get("key1", None)  # Access key1 to move it to the front
    cache.add("key3", "value3")  # This should evict key2
    assert cache.get("key2", None) is None
    assert cache.get("key1", None) == "value1"
    assert cache.get("key3", None) == "value3"


def test_thread_safety() -> None:
    cache = LRUCache(lock=threading.Lock(), max_capacity=10, ttl_seconds=10, on_remove=None)

    def add_items() -> None:
        for i in range(100):
            cache.add(f"key{i}", f"value{i}")
            time.sleep(0.01)

    threads = [threading.Thread(target=add_items) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(cache._map) <= 10  # Since max_capacity is 10, we should not exceed this


def test_multiprocessing_safety() -> None:
    cache = LRUCache(lock=multiprocessing.Lock(), max_capacity=10, ttl_seconds=10, on_remove=None)

    global add_items

    def add_items(_cache: LRUCache) -> None:
        for i in range(100):
            _cache.add(f"key{i}", f"value{i}")
            time.sleep(0.01)

    processes = [multiprocessing.Process(target=add_items, args=(cache,)) for _ in range(5)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    assert len(cache._map) <= 10  # Since max_capacity is 10, we should not exceed this
