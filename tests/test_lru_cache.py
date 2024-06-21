import math
import time

from py_lru import LRUCache


def test_add_new() -> None:
    cache: LRUCache = LRUCache(None, None, None)
    for i in range(10):
        assert cache.add(str(i), i) is None

    assert len(cache._lru) == 10

    for i in range(10):
        cache_entry = cache._lru.popleft()

        assert cache_entry.key == str(i)
        assert cache_entry.value == i
        assert math.isclose(cache_entry.ttl, time.time())


def test_add_existing() -> None:
    assert False


def test_remove() -> None:
    assert False


def test_remove_on_remove() -> None:
    assert False


def test_max_capacity() -> None:
    assert False


def test_max_capacity_on_remove() -> None:
    assert False


def test_ttl() -> None:
    assert False


def test_ttl_on_remove() -> None:
    assert False


def test_clear() -> None:
    assert False


def test_clear_on_remove() -> None:
    assert False


def test_get_existing() -> None:
    assert False


def test_get_missing() -> None:
    assert False
