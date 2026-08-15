from __future__ import annotations

from concurrency_bench.application.benchmarks import BenchmarkComparison, BenchmarkRunner
from concurrency_bench.application.use_cases import PurchaseProduct, RunExperiment
from concurrency_bench.domain.entities import Experiment, Product
from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.infrastructure.concurrency import ThreadStrategy
from concurrency_bench.infrastructure.database import build_engine, build_session_factory, reset_schema
from concurrency_bench.infrastructure.database.product_repository import SqlAlchemyProductRepository
from concurrency_bench.infrastructure.stock import InMemoryProductRepository, build_purchase_tasks
from sqlalchemy.exc import OperationalError


def _format_optional(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "n/d"
    return f"{value:.2f}{suffix}"


def _format_speedup(value: float | None) -> str:
    if value is None:
        return "n/d"
    return f"{value:.2f}x"


def _print_summary(summary, initial_stock: int, final_stock: int) -> None:
    run = summary.runs[-1]
    approved = sum(run.metadata["completed_results"])
    rejected = run.task_count - approved
    inconsistencies: list[str] = []

    if approved > initial_stock:
        inconsistencies.append(
            "mais compras aprovadas do que o estoque inicial")
    if final_stock < 0:
        inconsistencies.append("estoque final negativo")
    if final_stock != max(initial_stock - approved, 0):
        inconsistencies.append(
            "estoque final incompatível com as compras aprovadas")

    print(f"{summary.strategy_name}:")
    print(f"  estoque inicial: {initial_stock}")
    print(f"  tentativas: {run.task_count}")
    print(f"  aprovadas: {approved}")
    print(f"  rejeitadas: {rejected}")
    print(f"  estoque final: {final_stock}")
    print(f"  inconsistência: {'sim' if inconsistencies else 'não'}")
    if inconsistencies:
        print(f"  detalhes: {', '.join(inconsistencies)}")
    print(f"  tempo médio: {summary.elapsed.average:.4f}s")
    print(
        f"  throughput mediano: {summary.throughput.median:.2f} tentativas/s")
    cpu_value = summary.cpu_usage_percent.average if summary.cpu_usage_percent else None
    memory_value = summary.memory_usage_mb.average if summary.memory_usage_mb else None
    print(f"  cpu médio: {_format_optional(cpu_value, '%')}")
    print(f"  memória média: {_format_optional(memory_value, ' MB')}")
    print(
        f"  workers: {summary.workers_used if summary.workers_used is not None else 'n/d'}")
    print(f"  speedup: {_format_speedup(summary.speedup)}")
    print()


def _run_memory_scenario(*, use_lock: bool, label: str, runner: BenchmarkRunner) -> tuple[object, int]:
    initial_stock = 10
    attempts = 50
    state: dict[str, int] = {}

    def execute_once() -> object:
        repository = InMemoryProductRepository(
            use_lock=use_lock, interleave_delay_seconds=0.001)
        product = Product(name="Produto X", stock=initial_stock)
        repository.save(product)

        purchase = PurchaseProduct(repository, product.id)
        tasks = build_purchase_tasks(purchase.execute, attempt_count=attempts)
        experiment = Experiment(
            name=label,
            experiment_type=ExperimentType.DATABASE,
            task_count=attempts,
        )

        result = RunExperiment(ThreadStrategy(
            max_workers=10)).execute(experiment, tasks)
        final_stock = repository.get_stock(product.id)
        state["final_stock"] = -1 if final_stock is None else final_stock
        return result

    summary = runner.run(strategy_name=label, execute_once=execute_once)
    return summary, state.get("final_stock", -1)


def _run_postgres_scenario(runner: BenchmarkRunner) -> tuple[object | None, int]:
    initial_stock = 10
    attempts = 50
    engine = build_engine()
    try:
        reset_schema(engine)
        session_factory = build_session_factory(
            engine.url.render_as_string(hide_password=False))
        state: dict[str, int] = {}

        def execute_once() -> object:
            repository = SqlAlchemyProductRepository(session_factory)
            product = Product(name="Produto PostgreSQL", stock=initial_stock)
            repository.save(product)

            purchase = PurchaseProduct(repository, product.id)
            tasks = build_purchase_tasks(
                purchase.execute, attempt_count=attempts)
            experiment = Experiment(
                name="Estoque PostgreSQL",
                experiment_type=ExperimentType.DATABASE,
                task_count=attempts,
            )

            result = RunExperiment(ThreadStrategy(
                max_workers=10)).execute(experiment, tasks)
            final_stock = repository.get_stock(product.id)
            state["final_stock"] = -1 if final_stock is None else final_stock
            return result

        summary = runner.run(
            strategy_name="PostgreSQL com transação e lock de linha",
            execute_once=execute_once,
        )
        return summary, state.get("final_stock", -1)
    except OperationalError as error:
        print("PostgreSQL com transação e lock de linha")
        print(f"  indisponível: {error}")
        print()
        return None, -1
    finally:
        engine.dispose()


def main() -> None:
    runner = BenchmarkRunner(repetitions=3, warmup_runs=1)
    print("Stock concurrency comparison")
    print()
    summary, final_stock = _run_memory_scenario(
        use_lock=False, label="Memória sem Lock", runner=runner)
    _print_summary(summary, 10, final_stock)
    summary, final_stock = _run_memory_scenario(
        use_lock=True, label="Memória com Lock", runner=runner)
    _print_summary(summary, 10, final_stock)
    postgres_summary, final_stock = _run_postgres_scenario(runner)
    if postgres_summary is not None:
        _print_summary(postgres_summary, 10, final_stock)


if __name__ == "__main__":
    main()
