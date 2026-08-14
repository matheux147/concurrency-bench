from collections.abc import Sequence

from concurrency_lab.application.strategies import ExecutionStrategy, Task
from concurrency_lab.domain.entities import Experiment, ExperimentResult
from concurrency_lab.infrastructure.monitoring import ProcessMeasurement


class RunExperiment:
    """Orquestra uma execução sem conhecer sua estratégia concreta."""

    def __init__(self, strategy: ExecutionStrategy) -> None:
        self._strategy = strategy
        self._measurement = ProcessMeasurement()

    def execute(self, experiment: Experiment, tasks: Sequence[Task]) -> ExperimentResult:
        """Executa as tarefas e devolve as métricas básicas do experimento."""

        if len(tasks) != experiment.task_count:
            raise ValueError("A quantidade de tarefas deve corresponder ao experimento.")

        report, elapsed_seconds, usage = self._measurement.measure(
            lambda: self._strategy.execute(tasks)
        )

        return ExperimentResult(
            experiment_name=experiment.name,
            strategy=self._strategy.kind,
            task_count=len(tasks),
            completed_task_count=report.completed_count,
            total_time_seconds=elapsed_seconds,
            cpu_usage_percent=usage.cpu_usage_percent,
            memory_usage_mb=usage.memory_usage_mb,
            metadata={
                "completed_results": report.completed_results,
                "workers_used": report.workers_used,
            },
        )
