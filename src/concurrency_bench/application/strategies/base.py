from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from concurrency_bench.domain.enums import ExecutionStrategy as ExecutionStrategyType


Task = Callable[[], object]
AsyncTask = Callable[[], Awaitable[object]]


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Valores produzidos pela execução, na ordem em que foram concluídos."""

    completed_results: tuple[object, ...]
    workers_used: int | None = None

    @property
    def completed_count(self) -> int:
        return len(self.completed_results)


class ExecutionStrategy(Protocol):
    """Contrato para trocar o mecanismo de execução de um experimento.

    Este é o ponto de extensão do Strategy Pattern: um caso de uso poderá
    receber qualquer implementação compatível, sem conhecer se ela usa
    execução sequencial, threads, processos ou asyncio. As implementações
    concretas só serão adicionadas quando os experimentos forem introduzidos.
    """

    @property
    def kind(self) -> ExecutionStrategyType:
        """Identifica a estratégia para fins de resultado e observabilidade."""
        ...

    def execute(self, tasks: Sequence[Task]) -> ExecutionReport:
        """Executa as tarefas e devolve seus resultados na ordem de conclusão."""
        ...


class AsyncExecutionStrategy(Protocol):
    """Contrato para estratégias concorrentes baseadas em corrotinas."""

    @property
    def kind(self) -> ExecutionStrategyType:
        """Identifica a estratégia para fins de resultado e observabilidade."""
        ...

    async def execute(self, tasks: Sequence[AsyncTask]) -> ExecutionReport:
        """Executa corrotinas e devolve seus resultados na ordem de conclusão."""
        ...
