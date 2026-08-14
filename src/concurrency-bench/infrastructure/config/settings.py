import os
from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração mínima lida do ambiente, sem dependência de framework."""

    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return cls(database_url=database_url)

        user = _required_env("POSTGRES_USER")
        password = _required_env("POSTGRES_PASSWORD")
        database = _required_env("POSTGRES_DB")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = _read_port()

        encoded_user = quote(user, safe="")
        encoded_password = quote(password, safe="")
        encoded_database = quote(database, safe="")
        return cls(
            database_url=(
                f"postgresql://{encoded_user}:{encoded_password}"
                f"@{host}:{port}/{encoded_database}"
            )
        )


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"A variável de ambiente {name} é obrigatória.")
    return value


def _read_port() -> int:
    raw_port = os.getenv("POSTGRES_PORT", "5432")
    try:
        port = int(raw_port)
    except ValueError as error:
        raise ValueError("POSTGRES_PORT precisa ser um número inteiro.") from error
    if not 1 <= port <= 65535:
        raise ValueError("POSTGRES_PORT precisa estar entre 1 e 65535.")
    return port
