import pytest
from concurrency_bench.infrastructure.workloads.cache import InMemoryCache, build_cache_tasks


def test_cache_hits_and_misses() -> None:
    cache = InMemoryCache(use_lock=True, delay_seconds=0.0)

    # First get -> Miss
    val1 = cache.get("key1")
    assert val1 == "value_of_key1"
    assert cache.misses == 1
    assert cache.hits == 0

    # Second get -> Hit
    val2 = cache.get("key1")
    assert val2 == "value_of_key1"
    assert cache.misses == 1
    assert cache.hits == 1


def test_cache_clear_and_reset() -> None:
    cache = InMemoryCache(use_lock=True, delay_seconds=0.0)
    cache.get("key1")
    cache.get("key1")

    assert len(cache.data) == 1
    assert cache.hits == 1
    assert cache.misses == 1

    cache.reset_counters()
    assert cache.hits == 0
    assert cache.misses == 0
    assert len(cache.data) == 1

    cache.clear()
    assert cache.hits == 0
    assert cache.misses == 0
    assert len(cache.data) == 0


def test_build_cache_tasks() -> None:
    cache = InMemoryCache(use_lock=True, delay_seconds=0.0)
    tasks = build_cache_tasks(cache, "mykey", 5)

    assert len(tasks) == 5
    for task in tasks:
        assert task() == "value_of_mykey"

    assert cache.misses == 1
    assert cache.hits == 4
