import time
from typing import Generator
from unittest.mock import patch

from identity.utilities import (
    _get_raw_timestamp,
    get_instance,
    get_sequence,
    get_timestamp,
    id_generator,
    kodawari_epoch,
)


def get_bits_string(i: int) -> str:
    return bin(i)[2:]


def get_int_from_bits(bits: str) -> int:
    return int(bits, 2)


def test__get_raw_timestamp() -> None:
    timestamp_ms: int = 175841947
    id_with_timestamp: int = 737534581841921
    assert timestamp_ms == _get_raw_timestamp(id_with_timestamp)


def test_get_timestamp() -> None:
    expected_timestamp: int = 1674660671000
    id_with_timestamp: int = 737534581841921
    assert expected_timestamp == get_timestamp(id_with_timestamp)


def test_get_instance() -> None:
    instance: int = 42
    id_with_instance: int = 737534581841921
    assert get_instance(id_with_instance) == instance


def test_get_sequence():
    sequence: int = 1
    id: int = 737534581841921
    assert get_sequence(id) == sequence


def test_id_generator():
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

            actual_timestamp: int = _get_raw_timestamp(actual_id)
            actual_instance: int = get_instance(actual_id)
            actual_sequence: int = get_sequence(actual_id)

            assert expected_timestamp == actual_timestamp
            assert expected_instance == actual_instance
            assert expected_sequence == actual_sequence
            assert expected_id == actual_id
