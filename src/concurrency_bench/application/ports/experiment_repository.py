from typing import Protocol
from uuid import UUID

from concurrency_bench.domain.entities import Experiment


class ExperimentRepository(Protocol):
    """Porta mínima para persistir definições de experimento.

    O contrato fica na camada interna para que casos de uso não dependam de
    PostgreSQL ou de um ORM. A implementação concreta será criada quando a
    persistência fizer parte de um experimento real.
    """

    def save(self, experiment: Experiment) -> None:
        """Persiste ou atualiza um experimento."""
        ...

    def get_by_id(self, experiment_id: UUID) -> Experiment | None:
        """Recupera um experimento ou retorna ``None`` quando não existir."""
        ...
