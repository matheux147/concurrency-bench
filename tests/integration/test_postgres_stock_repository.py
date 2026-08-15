from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError

from concurrency_bench.application.use_cases import PurchaseProduct, RunExperiment
from concurrency_bench.domain.entities import Experiment, Product
from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.infrastructure.concurrency import ThreadStrategy
from concurrency_bench.infrastructure.database import (
    ProductModel,
    build_engine,
    build_session_factory,
    reset_schema,
)
from concurrency_bench.infrastructure.stock import build_purchase_tasks
from concurrency_bench.infrastructure.database.product_repository import SqlAlchemyProductRepository


@pytest.fixture(scope="module")
def database_engine():
    engine = build_engine()
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except OperationalError as error:
        pytest.skip(f"PostgreSQL indisponível: {error}")

    reset_schema(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(database_engine):
    return build_session_factory(database_engine.url.render_as_string(hide_password=False))


def test_postgres_repository_supports_purchase_and_readback(session_factory) -> None:
    repository = SqlAlchemyProductRepository(session_factory)
    product = Product(name="Produto P", stock=2)

    repository.save(product)

    stored = repository.get_by_id(product.id)
    assert stored is not None
    assert stored.stock == 2

    assert repository.purchase(product.id) is True
    assert repository.purchase(product.id) is True
    assert repository.purchase(product.id) is False

    assert repository.get_stock(product.id) == 0


def test_postgres_transaction_rolls_back_on_failure(session_factory) -> None:
    repository = SqlAlchemyProductRepository(session_factory)
    product = Product(name="Produto rollback", stock=3)
    repository.save(product)

    with session_factory() as session:
        with pytest.raises(RuntimeError, match="falha proposital"):
            with session.begin():
                row = session.get(ProductModel, product.id)
                assert row is not None
                row.stock -= 1
                raise RuntimeError("falha proposital")

    assert repository.get_stock(product.id) == 3


def test_postgres_concurrent_purchases_remain_consistent(session_factory) -> None:
    repository = SqlAlchemyProductRepository(session_factory)
    product = Product(name="Produto concorrente", stock=10)
    repository.save(product)

    purchase = PurchaseProduct(repository, product.id)
    tasks = build_purchase_tasks(purchase.execute, attempt_count=50)
    experiment = Experiment(
        name="Estoque PostgreSQL",
        experiment_type=ExperimentType.DATABASE,
        task_count=50,
    )

    result = RunExperiment(ThreadStrategy(max_workers=10)
                           ).execute(experiment, tasks)
    approved = sum(result.metadata["completed_results"])

    final_stock = repository.get_stock(product.id)
    assert final_stock is not None
    assert approved == 10
    assert final_stock == 0


def test_postgres_concurrent_purchases_without_lock_allows_inconsistency(session_factory) -> None:
    repository = SqlAlchemyProductRepository(
        session_factory,
        use_lock=False,
        interleave_delay_seconds=0.002,
    )
    product = Product(name="Produto concorrente sem lock", stock=10)
    repository.save(product)

    purchase = PurchaseProduct(repository, product.id)
    tasks = build_purchase_tasks(purchase.execute, attempt_count=50)
    experiment = Experiment(
        name="Estoque PostgreSQL Sem Lock",
        experiment_type=ExperimentType.DATABASE,
        task_count=50,
    )

    result = RunExperiment(ThreadStrategy(max_workers=10)
                           ).execute(experiment, tasks)
    approved = sum(result.metadata["completed_results"])

    final_stock = repository.get_stock(product.id)
    assert final_stock is not None
    # Without row lock, some purchases will be approved concurrently, leading to inconsistency
    # either approved > 10, or final_stock != 0, or final_stock < 0.
    inconsistent = (
        approved > 10
        or final_stock < 0
        or final_stock != max(10 - approved, 0)
    )
    assert inconsistent is True
