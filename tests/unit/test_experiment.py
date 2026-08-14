import pytest

from concurrency_lab.domain.entities import Experiment
from concurrency_lab.domain.enums import ExperimentType
from concurrency_lab.domain.exceptions import DomainValidationError


def test_experiment_keeps_identity_and_makes_parameters_immutable() -> None:
    parameters = {"delay_seconds": 0.1}
    experiment = Experiment(
        name="Leitura simulada",
        experiment_type=ExperimentType.IO_BOUND,
        task_count=4,
        parameters=parameters,
    )

    parameters["delay_seconds"] = 2.0

    assert experiment.name == "Leitura simulada"
    assert experiment.task_count == 4
    assert experiment.parameters["delay_seconds"] == 0.1

    with pytest.raises(TypeError):
        experiment.parameters["new_value"] = True  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", ""), ("name", "   "), ("task_count", 0), ("task_count", -1)],
)
def test_experiment_rejects_invalid_values(field: str, value: object) -> None:
    values: dict[str, object] = {
        "name": "Experimento válido",
        "experiment_type": ExperimentType.CUSTOM,
        "task_count": 1,
    }
    values[field] = value

    with pytest.raises(DomainValidationError):
        Experiment(**values)  # type: ignore[arg-type]
