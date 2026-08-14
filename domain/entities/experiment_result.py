from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from concurrency_lab.domain.enums import ExecutionStrategy
from concurrency_lab.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Representa as métricas essenciais produzidas por uma execução."""

    experiment_name: str
    strategy: ExecutionStrategy
    task_count: int
    completed_task_count: int
    total_time_seconds: float
    cpu_usage_percent: float | None = None
    memory_usage_mb: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.experiment_name.strip():
            raise DomainValidationError("O resultado precisa identificar o experimento.")
        if self.task_count < 0:
            raise DomainValidationError("A quantidade de tarefas não pode ser negativa.")
        if not 0 <= self.completed_task_count <= self.task_count:
            raise DomainValidationError(
                "A quantidade de tarefas concluídas deve estar entre zero e o total."
            )
        if self.total_time_seconds < 0:
            raise DomainValidationError("O tempo total não pode ser negativo.")
        if self.cpu_usage_percent is not None and self.cpu_usage_percent < 0:
            raise DomainValidationError("O uso de CPU não pode ser negativo.")
        if self.memory_usage_mb is not None and self.memory_usage_mb < 0:
            raise DomainValidationError("O uso de memória não pode ser negativo.")

        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def throughput_tasks_per_second(self) -> float:
        """Quantidade de tarefas concluídas por segundo."""

        if self.completed_task_count == 0 or self.total_time_seconds == 0:
            return 0.0
        return self.completed_task_count / self.total_time_seconds

    @property
    def average_task_time_seconds(self) -> float:
        """Tempo médio associado a cada tarefa."""

        if self.task_count == 0:
            return 0.0
        return self.total_time_seconds / self.task_count
