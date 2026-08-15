from collections.abc import Callable


def build_purchase_tasks(
    purchase_action: Callable[[], bool],
    attempt_count: int,
) -> list[Callable[[], bool]]:
    if attempt_count < 0:
        raise ValueError("attempt_count não pode ser negativo.")
    return [purchase_action for _ in range(attempt_count)]
