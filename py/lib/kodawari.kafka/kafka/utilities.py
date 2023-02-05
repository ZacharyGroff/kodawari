from json import JSONEncoder, dumps
from os import getenv
from typing import Any, Protocol, Type

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer


class EventProducer(Protocol):
    def produce(self, topic: str, key: str | bytes, value: str | bytes) -> None:
        ...


def get_event_producer(encoder_type: Type[JSONEncoder]) -> EventProducer:
    """Retrieves an EventProducer, configured for the current environment.

    Returns:
        An EventProducer object.
    Raises:
        Exception: KAFKA_BROKER_NAME is not set.
        Exception: KAFKA_BROKER_PORT is not set.
        Exception: MACHINE_INSTANCE_IDENTIFIER is not set.
    """
    kafka_broker_name: str | None = getenv("KAFKA_BROKER_NAME")
    if kafka_broker_name is None:
        raise Exception("KAFKA_BROKER_NAME is not set")

    kafka_broker_port: str | None = getenv("KAFKA_BROKER_PORT")
    if kafka_broker_port is None:
        raise Exception("KAFKA_BROKER_PORT is not set")

    machine_instance_identifier: str | None = getenv("MACHINE_INSTANCE_IDENTIFIER")
    if machine_instance_identifier is None:
        raise Exception("MACHINE_INSTANCE_IDENTIFIER is not set")

    kafka_config: dict[str, Any] = {
        "bootstrap.servers": f"{kafka_broker_name}:{kafka_broker_port}",
        "client.id": machine_instance_identifier,
        "key.serializer": StringSerializer("utf-8"),
        "value.serializer": lambda event, _: dumps(event, cls=encoder_type).encode(
            "utf-8"
        ),
    }
    return SerializingProducer(kafka_config)
