from __future__ import annotations

import asyncio

import httpx

from concurrency_lab.application.benchmarks import BenchmarkComparison, BenchmarkRunner
from concurrency_lab.application.use_cases import RunAsyncExperiment, RunExperiment
from concurrency_lab.domain.entities import Experiment
from concurrency_lab.domain.enums import ExperimentType
from concurrency_lab.infrastructure.concurrency import AsyncStrategy, SequentialStrategy, ThreadStrategy
from concurrency_lab.infrastructure.http import LocalDelayServer
from concurrency_lab.infrastructure.workloads import (
    HttpRequestPlan,
    build_http_async_tasks,
    build_http_sync_tasks,
)


def _format_optional(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "n/d"
    return f"{value:.2f}{suffix}"


def _format_speedup(value: float | None) -> str:
    if value is None:
        return "n/d"
    return f"{value:.2f}x"


def _print_summary(summary) -> None:
    print(f"{summary.strategy_name}:")
    print(f"  tempo médio: {summary.elapsed.average:.4f}s")
    print(f"  tempo mediano: {summary.elapsed.median:.4f}s")
    print(f"  tempo mínimo: {summary.elapsed.minimum:.4f}s")
    print(f"  tempo máximo: {summary.elapsed.maximum:.4f}s")
    print(f"  desvio-padrão: {_format_optional(summary.elapsed.standard_deviation, 's')}")
    print(f"  throughput médio: {summary.throughput.average:.2f} tarefas/s")
    print(f"  throughput mediano: {summary.throughput.median:.2f} tarefas/s")
    cpu_value = summary.cpu_usage_percent.average if summary.cpu_usage_percent else None
    memory_value = summary.memory_usage_mb.average if summary.memory_usage_mb else None
    print(f"  cpu médio: {_format_optional(cpu_value, '%')}")
    print(f"  memória média: {_format_optional(memory_value, ' MB')}")
    print(f"  workers: {summary.workers_used if summary.workers_used is not None else 'n/d'}")
    print(f"  speedup: {_format_speedup(summary.speedup)}")
    print()


def main() -> None:
    request_count = 20
    delay_ms = 100
    max_workers = 8
    runner = BenchmarkRunner(repetitions=3, warmup_runs=1)

    experiment = Experiment(
        name="I/O-bound HTTP local",
        experiment_type=ExperimentType.HTTP,
        task_count=request_count,
    )

    with LocalDelayServer() as server:
        plan = HttpRequestPlan(
            base_url=server.base_url,
            request_count=request_count,
            delay_ms=delay_ms,
        )

        summaries = []
        with httpx.Client(timeout=5.0) as sync_client:
            summaries.append(
                runner.run(
                    strategy_name=SequentialStrategy().kind.value,
                    execute_once=lambda: RunExperiment(SequentialStrategy()).execute(
                        experiment,
                        build_http_sync_tasks(plan, sync_client),
                    ),
                )
            )
            summaries.append(
                runner.run(
                    strategy_name=ThreadStrategy(max_workers=max_workers).kind.value,
                    execute_once=lambda: RunExperiment(
                        ThreadStrategy(max_workers=max_workers)
                    ).execute(
                        experiment,
                        build_http_sync_tasks(plan, sync_client),
                    ),
                )
            )

        async def run_async_once() -> object:
            async with httpx.AsyncClient(timeout=5.0) as async_client:
                return await RunAsyncExperiment(AsyncStrategy()).execute(
                    experiment,
                    build_http_async_tasks(plan, async_client),
                )

        summaries.append(
            runner.run(
                strategy_name=AsyncStrategy().kind.value,
                execute_once=lambda: asyncio.run(run_async_once()),
            )
        )

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="I/O-bound HTTP local",
        summaries=summaries,
        baseline_strategy=SequentialStrategy().kind.value,
    )

    print(comparison.scenario_name)
    print()
    for summary in comparison.summaries:
        _print_summary(summary)


if __name__ == "__main__":
    main()
