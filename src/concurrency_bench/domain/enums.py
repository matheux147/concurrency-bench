from enum import StrEnum


class ExperimentType(StrEnum):
    """Tipos de cenário que o laboratório poderá executar."""

    IO_BOUND = "io_bound"
    CPU_BOUND = "cpu_bound"
    DATABASE = "database"
    HTTP = "http"
    CACHE = "cache"
    CUSTOM = "custom"


class ExecutionStrategy(StrEnum):
    """Estratégias de execução previstas para os experimentos."""

    SEQUENTIAL = "sequential"
    THREADS = "threads"
    PROCESSES = "processes"
    ASYNC = "async"
