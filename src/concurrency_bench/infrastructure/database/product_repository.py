from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from concurrency_lab.application.ports import ProductRepository
from concurrency_lab.domain.entities import Product
from concurrency_lab.infrastructure.database.models import ProductModel, PurchaseModel


class SqlAlchemyProductRepository(ProductRepository):
    """Repositório de estoque com transação explícita e bloqueio de linha."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        use_lock: bool = True,
        interleave_delay_seconds: float = 0.0,
    ) -> None:
        self._session_factory = session_factory
        self._use_lock = use_lock
        self._interleave_delay_seconds = interleave_delay_seconds

    def save(self, product: Product) -> None:
        with self._session_factory() as session:
            with session.begin():
                existing = session.get(ProductModel, product.id)
                if existing is None:
                    session.add(
                        ProductModel(
                            id=product.id,
                            name=product.name,
                            stock=product.stock,
                        )
                    )
                else:
                    existing.name = product.name
                    existing.stock = product.stock

    def get_by_id(self, product_id: UUID) -> Product | None:
        with self._session_factory() as session:
            row = session.get(ProductModel, product_id)
            if row is None:
                return None
            return Product(id=row.id, name=row.name, stock=row.stock)

    def get_stock(self, product_id: UUID) -> int | None:
        with self._session_factory() as session:
            row = session.get(ProductModel, product_id)
            if row is None:
                return None
            return row.stock

    def purchase(self, product_id: UUID) -> bool:
        from time import sleep
        with self._session_factory() as session:
            with session.begin():
                if self._use_lock:
                    statement = (
                        select(ProductModel)
                        .where(ProductModel.id == product_id)
                        .with_for_update()
                    )
                    product = session.execute(statement).scalar_one_or_none()
                else:
                    product = session.get(ProductModel, product_id)

                if product is None or product.stock <= 0:
                    return False

                if self._interleave_delay_seconds > 0:
                    sleep(self._interleave_delay_seconds)

                product.stock -= 1
                session.add(PurchaseModel(product_id=product.id))
                return True
