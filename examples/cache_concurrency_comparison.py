from __future__ import annotations

import time
import threading
from concurrency_bench.application.benchmarks import BenchmarkRunner
from concurrency_bench.application.use_cases import RunExperiment
from concurrency_bench.domain.entities import Experiment
from concurrency_bench.domain.enums import ExperimentType
from concurrency_bench.infrastructure.concurrency import ThreadStrategy
from concurrency_bench.infrastructure.workloads.cache import InMemoryCache, build_cache_tasks


def _print_summary(summary, hits: int, misses: int) -> None:
    total = hits + misses
    ratio = (hits / total * 100.0) if total > 0 else 0.0
    print(f"{summary.strategy_name}:")
    print(f"  total de requisições: {total}")
    print(f"  cache hits: {hits}")
    print(f"  cache misses: {misses}")
    print(f"  hit ratio: {ratio:.1f}%")
    print(f"  tempo médio: {summary.elapsed.average:.4f}s")
    print(f"  tempo mediano: {summary.elapsed.median:.4f}s")
    print(f"  throughput médio: {summary.throughput.average:.2f} reqs/s")
    print()


def main() -> None:
    runner = BenchmarkRunner(repetitions=3, warmup_runs=1)
    attempts = 50
    workers = 10
    delay_sec = 0.1  # 100ms delay for DB/API simulation
    experiment = Experiment(
        name="Cache Concurrency Comparison",
        experiment_type=ExperimentType.CACHE,
        task_count=attempts,
    )
    print("Cache concurrency comparison")
    print("============================")
    print(f"Executando {attempts} requisições simultâneas com {workers} workers.")
    print(f"Latência da consulta física simulada: {delay_sec * 1000:.0f}ms.")
    print()

    # 1. Sem Cache
    class NoCache:
        def __init__(self, delay: float):
            self.delay = delay
            self.hits = 0
            self.misses = 0
            self._lock = threading.Lock()

        def get(self, key: str) -> str:
            with self._lock:
                self.misses += 1
            time.sleep(self.delay)
            return f"val_{key}"

    no_cache_obj = NoCache(delay_sec)

    def execute_once_no_cache():
        no_cache_obj.hits = 0
        no_cache_obj.misses = 0
        tasks = [lambda: no_cache_obj.get("key") for _ in range(attempts)]
        return RunExperiment(ThreadStrategy(max_workers=workers)).execute(experiment, tasks)

    summary_no_cache = runner.run(strategy_name="Sem Cache", execute_once=execute_once_no_cache)
    _print_summary(summary_no_cache, 0, attempts)

    # 2. Cache sem Lock (Frio)
    cache_frio = InMemoryCache(use_lock=False, delay_seconds=delay_sec)

    def execute_once_frio():
        cache_frio.clear()
        tasks = build_cache_tasks(cache_frio, "key", attempts)
        return RunExperiment(ThreadStrategy(max_workers=workers)).execute(experiment, tasks)

    summary_frio = runner.run(strategy_name="Cache sem Lock (Frio)", execute_once=execute_once_frio)
    _print_summary(summary_frio, cache_frio.hits, cache_frio.misses)

    # 3. Cache sem Lock (Quente)
    cache_quente = InMemoryCache(use_lock=False, delay_seconds=delay_sec)

    def execute_once_quente():
        cache_quente.clear()
        cache_quente.get("key")
        cache_quente.reset_counters()
        tasks = build_cache_tasks(cache_quente, "key", attempts)
        return RunExperiment(ThreadStrategy(max_workers=workers)).execute(experiment, tasks)

    summary_quente = runner.run(strategy_name="Cache sem Lock (Quente)", execute_once=execute_once_quente)
    _print_summary(summary_quente, cache_quente.hits, cache_quente.misses)

    # 4. Cache com Lock (Frio)
    cache_frio_l = InMemoryCache(use_lock=True, delay_seconds=delay_sec)

    def execute_once_frio_l():
        cache_frio_l.clear()
        tasks = build_cache_tasks(cache_frio_l, "key", attempts)
        return RunExperiment(ThreadStrategy(max_workers=workers)).execute(experiment, tasks)

    summary_frio_l = runner.run(strategy_name="Cache com Lock (Frio)", execute_once=execute_once_frio_l)
    _print_summary(summary_frio_l, cache_frio_l.hits, cache_frio_l.misses)

    # 5. Cache com Lock (Quente)
    cache_quente_l = InMemoryCache(use_lock=True, delay_seconds=delay_sec)

    def execute_once_quente_l():
        cache_quente_l.clear()
        cache_quente_l.get("key")
        cache_quente_l.reset_counters()
        tasks = build_cache_tasks(cache_quente_l, "key", attempts)
        return RunExperiment(ThreadStrategy(max_workers=workers)).execute(experiment, tasks)

    summary_quente_l = runner.run(strategy_name="Cache com Lock (Quente)", execute_once=execute_once_quente_l)
    _print_summary(summary_quente_l, cache_quente_l.hits, cache_quente_l.misses)


if __name__ == "__main__":
    main()
