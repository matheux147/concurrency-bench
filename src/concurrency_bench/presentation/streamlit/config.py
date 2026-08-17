import streamlit as st
from dataclasses import dataclass
from concurrency_bench.domain.enums import ExperimentType


@dataclass
class CPUConfig:
    task_count: int
    max_workers: int
    work_iterations: int
    repetitions: int
    strategies: list[str]


@dataclass
class HTTPConfig:
    request_count: int
    delay_ms: int
    max_workers: int
    repetitions: int
    strategies: list[str]


@dataclass
class StockConfig:
    initial_stock: int
    attempt_count: int
    max_workers: int
    repetitions: int
    scenarios: list[str]


@dataclass
class CacheConfig:
    delay_ms: int
    attempt_count: int
    max_workers: int
    repetitions: int
    scenarios: list[str]


def validate_cpu_params(strategies, task_count, max_workers, work_iterations, repetitions):
    errors = []
    if not strategies:
        errors.append("Selecione ao menos uma estratégia.")
    if task_count <= 0:
        errors.append("A quantidade de tarefas deve ser maior que zero.")
    if max_workers <= 0:
        errors.append("A quantidade de workers deve ser maior que zero.")
    if work_iterations <= 0:
        errors.append("A carga (iterações) deve ser maior que zero.")
    if repetitions <= 0:
        errors.append("O número de repetições deve ser maior que zero.")
    return errors


def validate_http_params(strategies, request_count, delay_ms, max_workers, repetitions):
    errors = []
    if not strategies:
        errors.append("Selecione ao menos uma estratégia.")
    if request_count <= 0:
        errors.append("A quantidade de requisições deve ser maior que zero.")
    if delay_ms < 0:
        errors.append("O atraso HTTP (ms) não pode ser negativo.")
    if max_workers <= 0:
        errors.append("A quantidade de workers deve ser maior que zero.")
    if repetitions <= 0:
        errors.append("O número de repetições deve ser maior que zero.")
    return errors


def validate_stock_params(scenarios, initial_stock, attempt_count, max_workers, repetitions):
    errors = []
    if not scenarios:
        errors.append("Selecione ao menos um cenário de estoque.")
    if initial_stock < 0:
        errors.append("O estoque inicial não pode ser negativo.")
    if attempt_count <= 0:
        errors.append("A quantidade de tentativas deve ser maior que zero.")
    if max_workers <= 0:
        errors.append("A concorrência (workers) deve ser maior que zero.")
    if repetitions <= 0:
        errors.append("O número de repetições deve ser maior que zero.")
    return errors


def validate_cache_params(scenarios, delay_ms, attempt_count, max_workers, repetitions):
    errors = []
    if not scenarios:
        errors.append("Selecione ao menos um cenário de cache.")
    if delay_ms < 0:
        errors.append("O delay do cache (ms) não pode ser negativo.")
    if attempt_count <= 0:
        errors.append("A quantidade de tentativas deve ser maior que zero.")
    if max_workers <= 0:
        errors.append("A concorrência (workers) deve ser maior que zero.")
    if repetitions <= 0:
        errors.append("O número de repetições deve ser maior que zero.")
    return errors


def render_config():
    st.sidebar.header("Configuração do Experimento")

    scenario = st.sidebar.selectbox(
        "Cenário",
        ["CPU-bound", "I/O-bound HTTP", "Stock / PostgreSQL", "Cache / Memória"],
        index=0
    )

    if scenario == "CPU-bound":
        st.sidebar.subheader("Estratégias")
        strategies = []
        if st.sidebar.checkbox("Sequential", value=True):
            strategies.append("sequential")
        if st.sidebar.checkbox("Threads", value=True):
            strategies.append("threads")
        if st.sidebar.checkbox("Processes", value=True):
            strategies.append("processes")

        st.sidebar.subheader("Parâmetros")
        task_count = st.sidebar.number_input(
            "Tarefas", min_value=-100, max_value=100000, value=6, step=1)
        max_workers = st.sidebar.number_input(
            "Workers", min_value=-100, max_value=256, value=2, step=1)
        work_iterations = st.sidebar.number_input(
            "Carga (Iterações)", min_value=-100000, max_value=10_000_000, value=100_000, step=10000)
        repetitions = st.sidebar.number_input(
            "Repetições do Benchmark", min_value=-10, max_value=50, value=3, step=1)

        validation_errors = validate_cpu_params(
            strategies, task_count, max_workers, work_iterations, repetitions)
        if validation_errors:
            for err in validation_errors:
                st.sidebar.error(err)
            return scenario, None, False

        return scenario, CPUConfig(
            task_count=task_count,
            max_workers=max_workers,
            work_iterations=work_iterations,
            repetitions=repetitions,
            strategies=strategies
        ), True

    elif scenario == "I/O-bound HTTP":
        st.sidebar.subheader("Estratégias")
        strategies = []
        if st.sidebar.checkbox("Sequential", value=True):
            strategies.append("sequential")
        if st.sidebar.checkbox("Threads", value=True):
            strategies.append("threads")
        if st.sidebar.checkbox("Asyncio", value=True):
            strategies.append("async")

        st.sidebar.subheader("Parâmetros")
        request_count = st.sidebar.number_input(
            "Requisições", min_value=-100, max_value=10000, value=20, step=1)
        delay_ms = st.sidebar.number_input(
            "Atraso HTTP (ms)", min_value=-1000, max_value=10000, value=100, step=50)
        max_workers = st.sidebar.number_input(
            "Workers (Threads)", min_value=-100, max_value=256, value=8, step=1)
        repetitions = st.sidebar.number_input(
            "Repetições do Benchmark", min_value=-10, max_value=50, value=3, step=1)

        validation_errors = validate_http_params(
            strategies, request_count, delay_ms, max_workers, repetitions)
        if validation_errors:
            for err in validation_errors:
                st.sidebar.error(err)
            return scenario, None, False

        return scenario, HTTPConfig(
            request_count=request_count,
            delay_ms=delay_ms,
            max_workers=max_workers,
            repetitions=repetitions,
            strategies=strategies
        ), True

    elif scenario == "Stock / PostgreSQL":
        st.sidebar.subheader("Cenários de Estoque")
        scenarios = []
        if st.sidebar.checkbox("Memória sem Lock", value=True):
            scenarios.append("Memória sem Lock")
        if st.sidebar.checkbox("Memória com Lock", value=True):
            scenarios.append("Memória com Lock")
        if st.sidebar.checkbox("PostgreSQL sem Lock", value=True):
            scenarios.append("PostgreSQL sem Lock")
        if st.sidebar.checkbox("PostgreSQL + transação + row lock", value=True):
            scenarios.append("PostgreSQL com transação e lock de linha")

        st.sidebar.subheader("Parâmetros")
        initial_stock = st.sidebar.number_input(
            "Estoque Inicial", min_value=-100, max_value=100000, value=10, step=1)
        attempt_count = st.sidebar.number_input(
            "Tentativas", min_value=-100, max_value=100000, value=50, step=5)
        max_workers = st.sidebar.number_input(
            "Concorrência (Workers)", min_value=-100, max_value=256, value=10, step=1)
        repetitions = st.sidebar.number_input(
            "Repetições do Benchmark", min_value=-10, max_value=50, value=3, step=1)

        validation_errors = validate_stock_params(
            scenarios, initial_stock, attempt_count, max_workers, repetitions)
        if validation_errors:
            for err in validation_errors:
                st.sidebar.error(err)
            return scenario, None, False

        return scenario, StockConfig(
            initial_stock=initial_stock,
            attempt_count=attempt_count,
            max_workers=max_workers,
            repetitions=repetitions,
            scenarios=scenarios
        ), True

    return scenario, None, False
