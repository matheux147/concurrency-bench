from collections.abc import Sequence

from concurrency_lab.application.strategies import AsyncExecutionStrategy, AsyncTask
from concurrency_lab.domain.entities import Experiment, ExperimentResult
from concurrency_lab.infrastructure.monitoring import ProcessMeasurement


class RunAsyncExperiment:
    """Orquestra um experimento assíncrono sem conhecer a infraestrutura."""

    def __init__(self, strategy: AsyncExecutionStrategy) -> None:
        self._strategy = strategy
        self._measurement = ProcessMeasurement()

    async def execute(
        self,
        experiment: Experiment,
        tasks: Sequence[AsyncTask],
    ) -> ExperimentResult:
        """Executa as corrotinas e devolve um resultado de domínio."""

        if len(tasks) != experiment.task_count:
            raise ValueError("A quantidade de tarefas deve corresponder ao experimento.")

        report, elapsed_seconds, usage = await self._measurement.measure_async(
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
