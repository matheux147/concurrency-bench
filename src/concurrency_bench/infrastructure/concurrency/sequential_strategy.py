from collections.abc import Sequence

from concurrency_bench.application.strategies import ExecutionReport, Task
from concurrency_bench.domain.enums import ExecutionStrategy as ExecutionStrategyType


class SequentialStrategy:
    """Executa cada tarefa no chamador, preservando a ordem recebida."""

    @property
    def kind(self) -> ExecutionStrategyType:
        return ExecutionStrategyType.SEQUENTIAL

    def execute(self, tasks: Sequence[Task]) -> ExecutionReport:
        """Executa todas as tarefas; qualquer exceção é propagada ao chamador."""

        completed_results = tuple(task() for task in tasks)
        return ExecutionReport(completed_results=completed_results, workers_used=1)
