from typing import Generator
from unittest.mock import patch

from pytest import raises

from identity.utilities import (
    _get_relative_timestamp,
    _machine_instance_identifier_environment_variable,
    get_id_generator,
    get_instance,
    get_sequence,
    get_timestamp,
    id_generator,
    kodawari_epoch,
)


def test__get_relative_timestamp() -> None:
    timestamp_ms: int = 175841947
    id_with_timestamp: int = 737534581841921
    assert timestamp_ms == _get_relative_timestamp(id_with_timestamp)


def test_get_timestamp() -> None:
    expected_timestamp: int = 1674660671000
    id_with_timestamp: int = 737534581841921
    assert expected_timestamp == get_timestamp(id_with_timestamp)


def test_get_instance() -> None:
    instance: int = 42
    id_with_instance: int = 737534581841921
    assert get_instance(id_with_instance) == instance


def test_get_sequence() -> None:
    sequence: int = 1
    id: int = 737534581841921
    assert get_sequence(id) == sequence


def test_id_generator() -> None:
    expected_id: int = 753611348905986
    expected_timestamp: int = 1674664504000 - kodawari_epoch
    expected_instance: int = 1
    expected_sequence: int = 2

    with patch("identity.utilities.time") as time_mock:
        with patch("identity.utilities.sleep") as _:
            time_mock.return_value = 1674664504

            generator: Generator[int, None, None] = id_generator(expected_instance)
            _: int = next(generator)
            _: int = next(generator)
            actual_id: int = next(generator)

            actual_timestamp: int = _get_relative_timestamp(actual_id)
            actual_instance: int = get_instance(actual_id)
            actual_sequence: int = get_sequence(actual_id)

            assert expected_timestamp == actual_timestamp
            assert expected_instance == actual_instance
            assert expected_sequence == actual_sequence
            assert expected_id == actual_id


def test_get_id_generator() -> None:
    with patch("identity.utilities.getenv") as getenv_mock:
        getenv_mock.return_value = "1"

        generator: Generator[int, None, None] = get_id_generator()

        assert generator is not None
        getenv_mock.assert_called_once_with(
            _machine_instance_identifier_environment_variable
        )


def test_get_id_generator_env_var_not_set() -> None:
    with patch("identity.utilities.getenv") as getenv_mock:
        getenv_mock.return_value = None

        with raises(Exception) as ex:
            _: Generator[int, None, None] = get_id_generator()
            assert "MACHINE_INSTANCE_IDENTIFIER is not set" == str(ex)

        getenv_mock.assert_called_once_with(
            _machine_instance_identifier_environment_variable
        )


def test_get_id_generator_env_var_not_int() -> None:
    with patch("identity.utilities.getenv") as getenv_mock:
        getenv_mock.return_value = "not int"

        with raises(Exception) as ex:
            _: Generator[int, None, None] = get_id_generator()
            assert "MACHINE_INSTANCE_IDENTIFIER cannot be casted to an integer" == str(
                ex
            )

        getenv_mock.assert_called_once_with(
            _machine_instance_identifier_environment_variable
        )
