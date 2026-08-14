import asyncio
from collections.abc import Sequence

from concurrency_lab.application.strategies import AsyncTask, ExecutionReport
from concurrency_lab.domain.enums import ExecutionStrategy as ExecutionStrategyType


class AsyncStrategy:
    """Executa corrotinas com ``asyncio.create_task`` e ``asyncio.gather``."""

    @property
    def kind(self) -> ExecutionStrategyType:
        return ExecutionStrategyType.ASYNC

    async def execute(self, tasks: Sequence[AsyncTask]) -> ExecutionReport:
        task_batch = tuple(tasks)
        scheduled_tasks = [asyncio.create_task(task()) for task in task_batch]
        results = tuple(await asyncio.gather(*scheduled_tasks))
        return ExecutionReport(completed_results=results, workers_used=None)
