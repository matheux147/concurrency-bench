from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4

from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class Experiment:
    """Descreve um experimento sem acoplar sua execução a uma estratégia."""

    name: str
    experiment_type: ExperimentType
    task_count: int
    description: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainValidationError("O experimento precisa ter um nome.")
        if self.task_count <= 0:
            raise DomainValidationError(
                "O experimento precisa ter pelo menos uma tarefa.")
        if self.created_at.tzinfo is None:
            raise DomainValidationError(
                "created_at precisa conter informação de fuso horário.")

        # A entidade é imutável também em relação aos parâmetros recebidos.
        object.__setattr__(self, "parameters",
                           MappingProxyType(dict(self.parameters)))
