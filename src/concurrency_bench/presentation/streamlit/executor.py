import asyncio
import json
from collections import defaultdict
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import httpx
from sqlalchemy.exc import OperationalError

from concurrency_bench.application.benchmarks import BenchmarkComparison, BenchmarkRunner, BenchmarkSummary
from concurrency_bench.application.use_cases import RunExperiment, RunAsyncExperiment, PurchaseProduct
from concurrency_bench.domain.entities import Experiment, Product, ExperimentResult
from concurrency_bench.domain.enums import ExperimentType, ExecutionStrategy
from concurrency_bench.infrastructure.concurrency import (
    SequentialStrategy,
    ThreadStrategy,
    ProcessStrategy,
    AsyncStrategy,
)
from concurrency_bench.infrastructure.workloads import (
    build_cpu_bound_tasks,
    HttpRequestPlan,
    build_http_sync_tasks,
    build_http_async_tasks,
)
from concurrency_bench.infrastructure.http import LocalDelayServer
from concurrency_bench.infrastructure.database import (
    build_engine,
    build_session_factory,
    reset_schema,
    SqlAlchemyExperimentRepository,
)
from concurrency_bench.infrastructure.database.product_repository import SqlAlchemyProductRepository
from concurrency_bench.infrastructure.stock import InMemoryProductRepository, build_purchase_tasks


def run_async_safe(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def save_experiment_to_db(experiment, comparison, stocks_map=None):
    engine = build_engine()
    try:
        reset_schema(engine)
        session_factory = build_session_factory(
            engine.url.render_as_string(hide_password=False))
        repository = SqlAlchemyExperimentRepository(session_factory)

        repository.save(experiment)

        results_to_save = []
        for summary in comparison.summaries:
            for run in summary.runs:
                run_meta = dict(run.metadata)
                run_meta["speedup"] = summary.speedup
                run_meta["workers_used"] = summary.workers_used
                if stocks_map and summary.strategy_name in stocks_map:
                    run_meta["final_stock"] = stocks_map[summary.strategy_name]

                run_updated = ExperimentResult(
                    experiment_name=run.experiment_name,
                    strategy=run.strategy,
                    task_count=run.task_count,
                    completed_task_count=run.completed_task_count,
                    total_time_seconds=run.total_time_seconds,
                    cpu_usage_percent=run.cpu_usage_percent,
                    memory_usage_mb=run.memory_usage_mb,
                    metadata=run_meta,
                    strategy_name=summary.strategy_name
                )
                results_to_save.append(run_updated)

        repository.save_results(experiment.id, results_to_save)
    except Exception:
        pass
    finally:
        engine.dispose()


def rebuild_comparison(experiment, results):
    by_strategy = defaultdict(list)
    for result in results:
        strat_key = result.strategy_name if result.strategy_name else (
            result.strategy.value if hasattr(result.strategy, "value") else str(result.strategy)
        )
        by_strategy[strat_key].append(result)

    summaries = []
    for strategy_name, runs in by_strategy.items():
        summary = BenchmarkSummary.from_results(strategy_name, runs)
        if runs:
            last_run = runs[-1]
            speedup = last_run.metadata.get("speedup")
            workers_used = last_run.metadata.get("workers_used")
            if speedup is not None or workers_used is not None:
                summary = replace(summary, speedup=speedup,
                                  workers_used=workers_used)
        summaries.append(summary)

    baseline = "sequential" if "sequential" in by_strategy else None

    return BenchmarkComparison.from_summaries(
        scenario_name=experiment.name,
        summaries=summaries,
        baseline_strategy=baseline,
    )


def load_experiment_history():
    engine = build_engine()
    try:
        session_factory = build_session_factory(
            engine.url.render_as_string(hide_password=False))
        repository = SqlAlchemyExperimentRepository(session_factory)

        history = repository.list_all()
        output = []
        for exp, results in history:
            comp = rebuild_comparison(exp, results)
            # Rebuild stocks_map if any
            stocks_map = {}
            for summary in comp.summaries:
                if summary.runs:
                    last_run = summary.runs[-1]
                    if "final_stock" in last_run.metadata:
                        stocks_map[summary.strategy_name] = last_run.metadata["final_stock"]

            output.append((exp, comp, stocks_map))
        return output
    except Exception:
        return []
    finally:
        engine.dispose()


def delete_experiment(experiment_id) -> None:
    engine = build_engine()
    try:
        session_factory = build_session_factory(
            engine.url.render_as_string(hide_password=False))
        repository = SqlAlchemyExperimentRepository(session_factory)
        repository.delete(experiment_id)
    except Exception:
        pass
    finally:
        engine.dispose()


def delete_all_experiments() -> None:
    engine = build_engine()
    try:
        session_factory = build_session_factory(
            engine.url.render_as_string(hide_password=False))
        repository = SqlAlchemyExperimentRepository(session_factory)
        repository.delete_all()
    except Exception:
        pass
    finally:
        engine.dispose()


def run_cpu_bound_experiment(config):
    runner = BenchmarkRunner(repetitions=config.repetitions, warmup_runs=1)
    experiment = Experiment(
        name="CPU-bound determinístico",
        experiment_type=ExperimentType.CPU_BOUND,
        task_count=config.task_count,
        parameters={
            "max_workers": config.max_workers,
            "work_iterations": config.work_iterations,
            "repetitions": config.repetitions,
        }
    )

    summaries = []
    for strat_name in config.strategies:
        if strat_name == "sequential":
            strategy = SequentialStrategy()
        elif strat_name == "threads":
            strategy = ThreadStrategy(max_workers=config.max_workers)
        elif strat_name == "processes":
            strategy = ProcessStrategy(max_workers=config.max_workers)
        else:
            continue

        summary = runner.run(
            strategy_name=strategy.kind.value,
            execute_once=lambda strategy=strategy: RunExperiment(strategy).execute(
                experiment,
                build_cpu_bound_tasks(
                    config.task_count, config.work_iterations),
            ),
        )
        summaries.append(summary)

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="CPU-bound determinístico",
        summaries=summaries,
        baseline_strategy="sequential",
    )

    save_experiment_to_db(experiment, comparison)
    return comparison


def run_io_bound_experiment(config):
    runner = BenchmarkRunner(repetitions=config.repetitions, warmup_runs=1)
    experiment = Experiment(
        name="I/O-bound HTTP local",
        experiment_type=ExperimentType.HTTP,
        task_count=config.request_count,
        parameters={
            "delay_ms": config.delay_ms,
            "max_workers": config.max_workers,
            "repetitions": config.repetitions,
        }
    )

    summaries = []

    with LocalDelayServer() as server:
        plan = HttpRequestPlan(
            base_url=server.base_url,
            request_count=config.request_count,
            delay_ms=config.delay_ms,
        )

        with httpx.Client(timeout=5.0) as sync_client:
            for strat_name in config.strategies:
                if strat_name == "sequential":
                    strategy = SequentialStrategy()
                    summary = runner.run(
                        strategy_name=strategy.kind.value,
                        execute_once=lambda strategy=strategy: RunExperiment(strategy).execute(
                            experiment,
                            build_http_sync_tasks(plan, sync_client),
                        ),
                    )
                    summaries.append(summary)
                elif strat_name == "threads":
                    strategy = ThreadStrategy(max_workers=config.max_workers)
                    summary = runner.run(
                        strategy_name=strategy.kind.value,
                        execute_once=lambda strategy=strategy: RunExperiment(strategy).execute(
                            experiment,
                            build_http_sync_tasks(plan, sync_client),
                        ),
                    )
                    summaries.append(summary)

        if "async" in config.strategies:
            async def run_async_once() -> object:
                async with httpx.AsyncClient(timeout=5.0) as async_client:
                    return await RunAsyncExperiment(AsyncStrategy()).execute(
                        experiment,
                        build_http_async_tasks(plan, async_client),
                    )

            summary = runner.run(
                strategy_name="async",
                execute_once=lambda: run_async_safe(run_async_once()),
            )
            summaries.append(summary)

    comparison = BenchmarkComparison.from_summaries(
        scenario_name="I/O-bound HTTP local",
        summaries=summaries,
        baseline_strategy="sequential",
    )

    save_experiment_to_db(experiment, comparison)
    return comparison


def run_stock_experiment(config):
    runner = BenchmarkRunner(repetitions=config.repetitions, warmup_runs=1)
    experiment = Experiment(
        name="Comparativo de Concorrência de Estoque",
        experiment_type=ExperimentType.DATABASE,
        task_count=config.attempt_count,
        parameters={
            "initial_stock": config.initial_stock,
            "attempt_count": config.attempt_count,
            "max_workers": config.max_workers,
            "repetitions": config.repetitions,
        }
    )
    results = []

    if "Memória sem Lock" in config.scenarios:
        state = {}

        def execute_once_no_lock():
            repository = InMemoryProductRepository(
                use_lock=False, interleave_delay_seconds=0.001)
            product = Product(name="Produto X", stock=config.initial_stock)
            repository.save(product)

            purchase = PurchaseProduct(repository, product.id)
            tasks = build_purchase_tasks(
                purchase.execute, attempt_count=config.attempt_count)

            result = RunExperiment(ThreadStrategy(
                max_workers=config.max_workers)).execute(experiment, tasks)
            final_stock = repository.get_stock(product.id)
            state["final_stock"] = -1 if final_stock is None else final_stock
            return result

        summary = runner.run(strategy_name="Memória sem Lock",
                             execute_once=execute_once_no_lock)
        results.append((summary, state.get("final_stock", -1)))

    if "Memória com Lock" in config.scenarios:
        state = {}

        def execute_once_with_lock():
            repository = InMemoryProductRepository(
                use_lock=True, interleave_delay_seconds=0.001)
            product = Product(name="Produto X", stock=config.initial_stock)
            repository.save(product)

            purchase = PurchaseProduct(repository, product.id)
            tasks = build_purchase_tasks(
                purchase.execute, attempt_count=config.attempt_count)

            result = RunExperiment(ThreadStrategy(
                max_workers=config.max_workers)).execute(experiment, tasks)
            final_stock = repository.get_stock(product.id)
            state["final_stock"] = -1 if final_stock is None else final_stock
            return result

        summary = runner.run(strategy_name="Memória com Lock",
                             execute_once=execute_once_with_lock)
        results.append((summary, state.get("final_stock", -1)))

    if "PostgreSQL sem Lock" in config.scenarios:
        engine = build_engine()
        try:
            reset_schema(engine)
            session_factory = build_session_factory(
                engine.url.render_as_string(hide_password=False))
            state = {}

            def execute_once_postgres_no_lock():
                repository = SqlAlchemyProductRepository(
                    session_factory,
                    use_lock=False,
                    interleave_delay_seconds=0.002,
                )
                product = Product(
                    name="Produto PostgreSQL Sem Lock", stock=config.initial_stock)
                repository.save(product)

                purchase = PurchaseProduct(repository, product.id)
                tasks = build_purchase_tasks(
                    purchase.execute, attempt_count=config.attempt_count)

                result = RunExperiment(ThreadStrategy(
                    max_workers=config.max_workers)).execute(experiment, tasks)
                final_stock = repository.get_stock(product.id)
                state["final_stock"] = - \
                    1 if final_stock is None else final_stock
                return result

            summary = runner.run(
                strategy_name="PostgreSQL sem Lock",
                execute_once=execute_once_postgres_no_lock,
            )
            results.append((summary, state.get("final_stock", -1)))
        except OperationalError as error:
            raise RuntimeError(
                f"PostgreSQL indisponível. Certifique-se de que o container Docker está em execução. Erro: {error}")
        finally:
            engine.dispose()

    if "PostgreSQL com transação e lock de linha" in config.scenarios:
        engine = build_engine()
        try:
            reset_schema(engine)
            session_factory = build_session_factory(
                engine.url.render_as_string(hide_password=False))
            state = {}

            def execute_once_postgres():
                repository = SqlAlchemyProductRepository(session_factory)
                product = Product(name="Produto PostgreSQL",
                                  stock=config.initial_stock)
                repository.save(product)

                purchase = PurchaseProduct(repository, product.id)
                tasks = build_purchase_tasks(
                    purchase.execute, attempt_count=config.attempt_count)

                result = RunExperiment(ThreadStrategy(
                    max_workers=config.max_workers)).execute(experiment, tasks)
                final_stock = repository.get_stock(product.id)
                state["final_stock"] = - \
                    1 if final_stock is None else final_stock
                return result

            summary = runner.run(
                strategy_name="PostgreSQL com transação e lock de linha",
                execute_once=execute_once_postgres,
            )
            results.append((summary, state.get("final_stock", -1)))
        except OperationalError as error:
            raise RuntimeError(
                f"PostgreSQL indisponível. Certifique-se de que o container Docker está em execução. Erro: {error}")
        finally:
            engine.dispose()

    summaries = [r[0] for r in results]
    comparison = BenchmarkComparison.from_summaries(
        scenario_name="Comparativo de Concorrência de Estoque",
        summaries=summaries,
        baseline_strategy=None
    )

    stocks_map = {r[0].strategy_name: r[1] for r in results}
    save_experiment_to_db(experiment, comparison, stocks_map)
    return comparison, stocks_map
