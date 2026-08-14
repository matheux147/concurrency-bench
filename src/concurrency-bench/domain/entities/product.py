from dataclasses import dataclass, field
from uuid import UUID, uuid4

from concurrency_lab.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class Product:
    """Produto simples com estoque controlado para experimentos concorrentes."""

    name: str
    stock: int
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainValidationError("O produto precisa ter um nome.")
        if self.stock < 0:
            raise DomainValidationError("O estoque não pode ser negativo.")
