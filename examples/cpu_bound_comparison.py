from concurrency_lab.application.benchmarks import BenchmarkComparison, BenchmarkRunner
from concurrency_lab.application.use_cases import RunExperiment
from concurrency_lab.domain.entities import Experiment
from concurrency_lab.domain.enums import ExperimentType
from concurrency_lab.infrastructure.concurrency import (
    ProcessStrategy,
    SequentialStrategy,
    ThreadStrategy,
)
from concurrency_lab.infrastructure.workloads import build_cpu_bound_tasks


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
    task_count = 6
    work_iterations = 100_000
    max_workers = 2
    runner = BenchmarkRunner(repetitions=3, warmup_runs=1)
    experiment = Experiment(
        name="CPU-bound determinístico",
        experiment_type=ExperimentType.CPU_BOUND,
        task_count=task_count,
    )

    strategies = (
        SequentialStrategy(),
        ThreadStrategy(max_workers=max_workers),
        ProcessStrategy(max_workers=max_workers),
    )

    summaries = []
    for strategy in strategies:
        summary = runner.run(
            strategy_name=strategy.kind.value,
            execute_once=lambda strategy=strategy: RunExperiment(strategy).execute(
                experiment,
                build_cpu_bound_tasks(task_count, work_iterations),
            ),
        )
        summaries.append(summary)

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="CPU-bound determinístico",
        summaries=summaries,
        baseline_strategy=SequentialStrategy().kind.value,
    )

    print(comparison.scenario_name)
    print()
    for summary in comparison.summaries:
        _print_summary(summary)


if __name__ == "__main__":
    main()
