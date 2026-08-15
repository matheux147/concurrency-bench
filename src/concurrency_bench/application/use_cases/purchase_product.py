from uuid import UUID

from concurrency_bench.application.ports import ProductRepository


class PurchaseProduct:
    """Orquestra uma compra individual sem conhecer a infraestrutura."""

    def __init__(self, repository: ProductRepository, product_id: UUID) -> None:
        self._repository = repository
        self._product_id = product_id

    def execute(self) -> bool:
        return self._repository.purchase(self._product_id)
