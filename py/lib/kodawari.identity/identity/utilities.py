from time import sleep, time
from typing import Generator

kodawari_epoch: int = 1674484829053
_total_bits: int = 64
_unused_sign_bits: int = 1
_timestamp_bits: int = 41
_instance_bits: int = 10
_sequence_bits: int = 12
_max_instances: int = (2**_instance_bits) - 1
_max_sequences: int = (2**_sequence_bits) - 1


def _get_raw_timestamp(id: int) -> int:
    return id >> (_instance_bits + _sequence_bits)


def get_timestamp(id: int) -> int:
    return _get_raw_timestamp(id) + kodawari_epoch


def get_instance(id: int) -> int:
    timestamp: int = _get_raw_timestamp(id)
    return (id ^ (timestamp << (_instance_bits + _sequence_bits))) >> _sequence_bits


def get_sequence(id: int) -> int:
    timestamp: int = _get_raw_timestamp(id)
    instance: int = get_instance(id)
    return (
        id
        ^ (instance << _sequence_bits)
        ^ (timestamp << (_instance_bits + _sequence_bits))
    )


def id_generator(instance_id: int) -> Generator[int, None, None]:
    if instance_id < 0 or instance_id > _max_instances:
        raise Exception("Invalid instance_id")

    previous_timestamp: int | None = None
    sequence: int = 0

    while True:
        current_timestamp: int = int(time() * 1000) - kodawari_epoch
        if previous_timestamp is not None and previous_timestamp == current_timestamp:
            if sequence > _max_sequences:
                sleep(1)
                sequence = 0
            else:
                sequence += 1
        else:
            sequence = 0

        previous_timestamp = current_timestamp

        shifted_timestamp: int = current_timestamp << _instance_bits
        id: int = ((shifted_timestamp | instance_id) << _sequence_bits) | sequence
        yield id
