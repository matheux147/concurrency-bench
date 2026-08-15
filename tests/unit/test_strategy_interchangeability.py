from concurrency_bench.application.use_cases import RunExperiment
from concurrency_bench.domain.entities import Experiment
from concurrency_bench.domain.enums import ExperimentType, ExecutionStrategy
from concurrency_bench.infrastructure.concurrency import (
    ProcessStrategy,
    SequentialStrategy,
    ThreadStrategy,
)
from concurrency_bench.infrastructure.workloads import build_cpu_bound_tasks


def test_run_experiment_accepts_all_current_strategies() -> None:
    experiment = Experiment(
        name="Comparação pequena",
        experiment_type=ExperimentType.CPU_BOUND,
        task_count=3,
    )

    strategies = (
        (SequentialStrategy(), ExecutionStrategy.SEQUENTIAL),
        (ThreadStrategy(max_workers=2), ExecutionStrategy.THREADS),
        (ProcessStrategy(max_workers=2), ExecutionStrategy.PROCESSES),
    )

    for strategy, expected_kind in strategies:
        result = RunExperiment(strategy).execute(
            experiment,
            build_cpu_bound_tasks(task_count=3, work_iterations=100),
        )

        assert result.strategy is expected_kind
        assert result.completed_task_count == 3
        assert result.metadata["completed_results"]
