from typing import Protocol
from uuid import UUID

from concurrency_lab.domain.entities import Product


class ProductRepository(Protocol):
    """Porta mínima para manipular estoque persistido ou em memória."""

    def save(self, product: Product) -> None:
        """Persiste um produto inicial ou atualizado."""
        ...

    def get_by_id(self, product_id: UUID) -> Product | None:
        """Recupera um produto pelo identificador."""
        ...

    def get_stock(self, product_id: UUID) -> int | None:
        """Lê o estoque atual sem converter para a entidade de domínio."""
        ...

    def purchase(self, product_id: UUID) -> bool:
        """Tenta comprar uma unidade do produto, devolvendo sucesso ou falha."""
        ...
