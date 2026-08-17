import time
import threading
from collections.abc import Callable


class InMemoryCache:
    def __init__(self, use_lock: bool, delay_seconds: float = 0.1):
        self.use_lock = use_lock
        self.delay = delay_seconds
        self.data = {}
        self.lock = threading.Lock()
        self._lock_hits = threading.Lock()
        self._lock_misses = threading.Lock()
        self.hits = 0
        self.misses = 0

    def reset_counters(self) -> None:
        with self._lock_hits:
            self.hits = 0
        with self._lock_misses:
            self.misses = 0

    def clear(self) -> None:
        self.data.clear()
        self.reset_counters()

    def get(self, key: str) -> str:
        if self.use_lock:
            with self.lock:
                return self._get_impl(key)
        else:
            return self._get_impl(key)

    def _get_impl(self, key: str) -> str:
        if key in self.data:
            with self._lock_hits:
                self.hits += 1
            return self.data[key]

        with self._lock_misses:
            self.misses += 1
        time.sleep(self.delay)
        val = f"value_of_{key}"
        self.data[key] = val
        return val


def masbuild_cache_tasks(
    cache: InMemoryCache,
    key: str,
    count: int,
) -> list[Callable[[], str]]:
    return [lambda cache=cache, key=key: cache.get(key) for _ in range(count)]
