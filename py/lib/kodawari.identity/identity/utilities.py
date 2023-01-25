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
    """Retrieves a timestamp, relative to kodawari_epoch, given an id.

    Retrieves a unix timestamp in milliseconds, representing the time the given id was created subtracted by kodawari_epoch.

    Args:
        id: An id issued by id_generator.

    Returns:
        The duration milliseconds from kodawari_epoch until id was generated.
    """
    return id >> (_instance_bits + _sequence_bits)


def get_timestamp(id: int) -> int:
    """Retrieves a timestamp given an id.

    Retrieves a unix timestamp in milliseconds, representing the time the given id was created.

    Args:
        id: An id issued by id_generator.

    Returns:
        The int unix timestamp in milliseconds, representing the time the id was created.
    """
    return _get_raw_timestamp(id) + kodawari_epoch


def get_instance(id: int) -> int:
    """Retrieves an instance given an id.

    Retrieves an instance, representing the identifier of the machine that requested id, from id.

    Args:
        id: An id issued by id_generator.

    Returns:
        The int representing the identifier of the machine that requested id.
    """
    timestamp: int = _get_raw_timestamp(id)
    return (id ^ (timestamp << (_instance_bits + _sequence_bits))) >> _sequence_bits


def get_sequence(id: int) -> int:
    """Retrieves a sequence given an id.

    Retrieves a sequence, representing the number of ids generated at the same millisecond as id at the time id was generated, from id.

    Args:
        id: An id issued by id_generator.

    Returns:
        The int representing the number of ids generated at the same millisecond as id at the time id was generated.
    """
    timestamp: int = _get_raw_timestamp(id)
    instance: int = get_instance(id)
    return (
        id
        ^ (instance << _sequence_bits)
        ^ (timestamp << (_instance_bits + _sequence_bits))
    )


def id_generator(instance_id: int) -> Generator[int, None, None]:
    """Yields a unique, time-sortable, integer identifier.

    Generates an identifier that is unique and time-sortable, using the current unix timestamp in milliseconds, kodawari_epoch, the identifier of the machine requesting an id, and the count of identifiers generated during the current millisecond.

    Args:
        instance_id: The identifier of the machine issuing the request to generate an identifier.

    Yields:
        A unique, time sortable, integer identifier. The identifier's first bit is an unused sign bit, the next 41 bits represent the number of milliseconds since kodawari_epoch, the following 10 bits represent the identifer of the machine that requested the id, the last 12 bits represent the number of ids generated at the same millisecond as the identifier at the time the identifier was generated. For example:

        identifier = 753611348905986 = [0] [000000000000010101011010110011111010000110] [000000001] [000000000010]
        sign_bit = [0]
        timestamp = [000000000000010101011010110011111010000110] = 1674664504000 - kodawari_epoch
        instance_id = [000000001] = 1
        sequence_id = [000000000010] = 2

    Raises:
        Exception: Invalid instance_id.
    """
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
