from __future__ import annotations

from dataclasses import dataclass, replace
from statistics import median, stdev
from typing import Iterable

from concurrency_bench.domain.entities import ExperimentResult


@dataclass(frozen=True, slots=True)
class StatisticalSummary:
    average: float
    median: float
    minimum: float
    maximum: float
    standard_deviation: float | None = None

    @classmethod
    def from_values(cls, values: Iterable[float]) -> "StatisticalSummary":
        items = tuple(values)
        if not items:
            raise ValueError("É necessário informar ao menos um valor.")
        return cls(
            average=sum(items) / len(items),
            median=median(items),
            minimum=min(items),
            maximum=max(items),
            standard_deviation=stdev(items) if len(items) > 1 else None,
        )


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    strategy_name: str
    runs: tuple[ExperimentResult, ...]
    elapsed: StatisticalSummary
    throughput: StatisticalSummary
    cpu_usage_percent: StatisticalSummary | None
    memory_usage_mb: StatisticalSummary | None
    workers_used: int | None
    speedup: float | None = None

    @classmethod
    def from_results(
        cls,
        strategy_name: str,
        runs: Iterable[ExperimentResult],
    ) -> "BenchmarkSummary":
        items = tuple(runs)
        if not items:
            raise ValueError("É necessário informar ao menos um resultado.")

        elapsed = StatisticalSummary.from_values(
            result.total_time_seconds for result in items)
        throughput = StatisticalSummary.from_values(
            result.throughput_tasks_per_second for result in items
        )
        cpu_values = [
            result.cpu_usage_percent for result in items if result.cpu_usage_percent is not None]
        memory_values = [
            result.memory_usage_mb for result in items if result.memory_usage_mb is not None
        ]
        workers_used = next(
            (
                result.metadata.get("workers_used")
                for result in items
                if isinstance(result.metadata.get("workers_used"), int)
            ),
            None,
        )

        return cls(
            strategy_name=strategy_name,
            runs=items,
            elapsed=elapsed,
            throughput=throughput,
            cpu_usage_percent=(
                StatisticalSummary.from_values(
                    cpu_values) if cpu_values else None
            ),
            memory_usage_mb=(
                StatisticalSummary.from_values(
                    memory_values) if memory_values else None
            ),
            workers_used=workers_used,
        )

    def with_speedup(self, baseline_elapsed_seconds: float | None) -> "BenchmarkSummary":
        if baseline_elapsed_seconds is None or baseline_elapsed_seconds <= 0:
            return replace(self, speedup=None)
        if self.elapsed.median <= 0:
            return replace(self, speedup=None)
        return replace(self, speedup=baseline_elapsed_seconds / self.elapsed.median)


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    scenario_name: str
    summaries: tuple[BenchmarkSummary, ...]

    @classmethod
    def from_summaries(
        cls,
        scenario_name: str,
        summaries: Iterable[BenchmarkSummary],
        baseline_strategy: str | None,
    ) -> "BenchmarkComparison":
        items = tuple(summaries)
        baseline_elapsed = None
        if baseline_strategy is not None:
            for summary in items:
                if summary.strategy_name == baseline_strategy:
                    baseline_elapsed = summary.elapsed.median
                    break

        return cls(
            scenario_name=scenario_name,
            summaries=tuple(
                summary.with_speedup(baseline_elapsed)
                for summary in items
            ),
        )
