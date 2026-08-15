from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import sleep
from uuid import UUID

from concurrency_lab.application.ports import ProductRepository
from concurrency_lab.domain.entities import Product


@dataclass(slots=True)
class _ProductRecord:
    id: UUID
    name: str
    stock: int


class InMemoryProductRepository(ProductRepository):
    """Repositório em memória para demonstrar corrida e proteção com Lock."""

    def __init__(
        self,
        *,
        use_lock: bool,
        interleave_delay_seconds: float = 0.001,
    ) -> None:
        self._use_lock = use_lock
        self._interleave_delay_seconds = interleave_delay_seconds
        self._lock = Lock()
        self._records: dict[UUID, _ProductRecord] = {}

    def save(self, product: Product) -> None:
        self._records[product.id] = _ProductRecord(
            id=product.id,
            name=product.name,
            stock=product.stock,
        )

    def get_by_id(self, product_id: UUID) -> Product | None:
        record = self._records.get(product_id)
        if record is None:
            return None
        if record.stock < 0:
            return None
        return Product(id=record.id, name=record.name, stock=record.stock)

    def get_stock(self, product_id: UUID) -> int | None:
        record = self._records.get(product_id)
        if record is None:
            return None
        return record.stock

    def purchase(self, product_id: UUID) -> bool:
        if self._use_lock:
            with self._lock:
                return self._purchase_without_lock(product_id)
        return self._purchase_without_lock(product_id)

    def _purchase_without_lock(self, product_id: UUID) -> bool:
        record = self._records.get(product_id)
        if record is None:
            return False
        if record.stock <= 0:
            return False

        sleep(self._interleave_delay_seconds)
        record.stock -= 1
        return True
