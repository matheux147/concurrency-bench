from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor

from concurrency_bench.application.strategies import ExecutionReport, Task
from concurrency_bench.domain.enums import ExecutionStrategy as ExecutionStrategyType


class ProcessStrategy:
    """Executa tarefas usando ``ProcessPoolExecutor``."""

    def __init__(self, max_workers: int | None = None) -> None:
        _validate_max_workers(max_workers)
        self._max_workers = max_workers

    @property
    def kind(self) -> ExecutionStrategyType:
        return ExecutionStrategyType.PROCESSES

    def execute(self, tasks: Sequence[Task]) -> ExecutionReport:
        """Executa tarefas serializáveis e propaga exceções dos workers."""

        task_batch = tuple(tasks)
        with ProcessPoolExecutor(max_workers=self._max_workers) as executor:
            results = tuple(executor.map(_run_task, task_batch))

        return ExecutionReport(
            completed_results=results,
            workers_used=self._max_workers,
        )


def _run_task(task: Task) -> object:
    return task()


def _validate_max_workers(max_workers: int | None) -> None:
    if max_workers is not None and max_workers <= 0:
        raise ValueError("max_workers deve ser maior que zero.")
