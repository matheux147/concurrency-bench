from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from os import cpu_count
from time import perf_counter
from typing import TypeVar

import psutil

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ProcessUsage:
    """Métricas simples do processo atual."""

    cpu_usage_percent: float | None
    memory_usage_mb: float | None


@dataclass(frozen=True, slots=True)
class ProcessSample:
    cpu_time_seconds: float
    rss_bytes: int


def capture_process_usage() -> ProcessSample:
    process = psutil.Process()
    cpu_times = process.cpu_times()
    memory_info = process.memory_info()
    return ProcessSample(
        cpu_time_seconds=cpu_times.user + cpu_times.system,
        rss_bytes=memory_info.rss,
    )


def build_process_usage(
    before: ProcessSample,
    after: ProcessSample,
    elapsed_seconds: float,
) -> ProcessUsage:
    if elapsed_seconds <= 0:
        return ProcessUsage(
            cpu_usage_percent=None,
            memory_usage_mb=after.rss_bytes / (1024 * 1024),
        )

    cpu_seconds = max(after.cpu_time_seconds - before.cpu_time_seconds, 0.0)
    total_cpus = cpu_count() or 1
    cpu_usage_percent = (cpu_seconds / elapsed_seconds / total_cpus) * 100
    memory_usage_mb = max(before.rss_bytes, after.rss_bytes) / (1024 * 1024)
    return ProcessUsage(cpu_usage_percent=cpu_usage_percent, memory_usage_mb=memory_usage_mb)


class ProcessMeasurement:
    """Mede duração e coleta métricas do processo de forma centralizada."""

    def measure(self, operation: Callable[[], T]) -> tuple[T, float, ProcessUsage]:
        before = capture_process_usage()
        started_at = perf_counter()
        result = operation()
        elapsed_seconds = perf_counter() - started_at
        after = capture_process_usage()
        usage = build_process_usage(before, after, elapsed_seconds)
        return result, elapsed_seconds, usage

    async def measure_async(
        self,
        operation: Callable[[], Awaitable[T]],
    ) -> tuple[T, float, ProcessUsage]:
        before = capture_process_usage()
        started_at = perf_counter()
        result = await operation()
        elapsed_seconds = perf_counter() - started_at
        after = capture_process_usage()
        usage = build_process_usage(before, after, elapsed_seconds)
        return result, elapsed_seconds, usage
