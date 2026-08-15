import pandas as pd
from concurrency_bench.application.benchmarks.models import BenchmarkComparison


def _format_optional_float(val: float | None, fmt: str, fallback: str = "N/D") -> str:
    if val is None:
        return fallback
    return fmt.format(val)


def _format_optional_int(val: int | None, fallback: str = "N/D") -> str:
    if val is None:
        return fallback
    return str(val)


def build_comparison_table(comparison: BenchmarkComparison) -> pd.DataFrame:
    data = []
    for summary in comparison.summaries:
        cpu_avg = summary.cpu_usage_percent.average if summary.cpu_usage_percent else None
        mem_avg = summary.memory_usage_mb.average if summary.memory_usage_mb else None

        data.append({
            "Estratégia": summary.strategy_name,
            "Tempo Médio (s)": _format_optional_float(summary.elapsed.average, "{:.4f}s"),
            "Tempo Mediano (s)": _format_optional_float(summary.elapsed.median, "{:.4f}s"),
            "Throughput Médio (tarefas/s)": _format_optional_float(summary.throughput.average, "{:.2f}"),
            "Speedup": _format_optional_float(summary.speedup, "{:.2f}x"),
            "CPU Médio": _format_optional_float(cpu_avg, "{:.2f}%"),
            "Memória Média": _format_optional_float(mem_avg, "{:.2f} MB"),
            "Workers": _format_optional_int(summary.workers_used),
        })

    return pd.DataFrame(data)


def build_stock_table(comparison: BenchmarkComparison, stocks_map: dict[str, int], initial_stock: int) -> pd.DataFrame:
    data = []
    for summary in comparison.summaries:
        run = summary.runs[-1]
        approved = sum(run.metadata["completed_results"])
        attempts = run.task_count
        rejected = attempts - approved
        final_stock = stocks_map.get(summary.strategy_name, -1)

        inconsistencies = []
        if approved > initial_stock:
            inconsistencies.append("mais aprovadas que estoque inicial")
        if final_stock < 0:
            inconsistencies.append("estoque final negativo")
        if final_stock != max(initial_stock - approved, 0):
            inconsistencies.append("estoque incompatível")

        inconsistent_str = "Sim (" + ", ".join(inconsistencies) + \
            ")" if inconsistencies else "Não"

        data.append({
            "Cenário": summary.strategy_name,
            "Estoque Inicial": initial_stock,
            "Tentativas": attempts,
            "Aprovadas": approved,
            "Rejeitadas": rejected,
            "Estoque Final": final_stock,
            "Inconsistência": inconsistent_str,
            "Tempo Médio (s)": f"{summary.elapsed.average:.4f}s",
            "Throughput Médio (tentativas/s)": f"{summary.throughput.average:.2f}",
        })

    return pd.DataFrame(data)
