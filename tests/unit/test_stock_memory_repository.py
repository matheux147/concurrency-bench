from concurrency_bench.application.use_cases import PurchaseProduct, RunExperiment
from concurrency_bench.domain.entities import Product
from concurrency_bench.domain.entities import Experiment
from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.infrastructure.concurrency import ThreadStrategy
from concurrency_bench.infrastructure.stock import InMemoryProductRepository, build_purchase_tasks


def test_in_memory_repository_handles_basic_purchase_flow() -> None:
    repository = InMemoryProductRepository(
        use_lock=True, interleave_delay_seconds=0.0)
    product = Product(name="Produto X", stock=2)
    repository.save(product)

    assert repository.purchase(product.id) is True
    assert repository.purchase(product.id) is True
    assert repository.purchase(product.id) is False
    assert repository.get_stock(product.id) == 0


def test_purchase_use_case_delegates_to_repository() -> None:
    class FakeRepository:
        def __init__(self) -> None:
            self.received_product_ids: list[object] = []

        def purchase(self, product_id: object) -> bool:
            self.received_product_ids.append(product_id)
            return True

    repository = FakeRepository()
    product = Product(name="Produto Y", stock=1)

    assert PurchaseProduct(repository, product.id).execute() is True
    assert repository.received_product_ids == [product.id]


def test_locked_memory_repository_remains_consistent_with_threads() -> None:
    repository = InMemoryProductRepository(
        use_lock=True, interleave_delay_seconds=0.001)
    product = Product(name="Produto Z", stock=10)
    repository.save(product)

    purchase_use_case = PurchaseProduct(repository, product.id)
    tasks = build_purchase_tasks(purchase_use_case.execute, attempt_count=50)
    experiment = Experiment(name="Estoque em memória",
                            experiment_type=ExperimentType.CUSTOM, task_count=50)

    result = RunExperiment(ThreadStrategy(max_workers=10)
                           ).execute(experiment, tasks)

    approved = sum(result.metadata["completed_results"])
    final_stock = repository.get_stock(product.id)

    assert result.completed_task_count == 50
    assert approved == 10
    assert final_stock == 0
