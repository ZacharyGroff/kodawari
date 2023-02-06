from unittest.mock import call, patch

from kafka.models import RecipeEventEncoder
from kafka.utilities import EventProducer, get_event_producer


def test_get_event_producer() -> None:
    with patch("kafka.utilities.getenv") as getenv_mock:
        with patch("kafka.utilities.SerializingProducer") as serializing_producer_mock:
            expected_serializing_producer_return_value: str = "test"
            serializing_producer_mock.return_value = (
                expected_serializing_producer_return_value
            )
            getenv_mock.return_value = "test-env-var"
            producer: EventProducer = get_event_producer(
                RecipeEventEncoder, error_cb=lambda x: print(x)
            )

            assert expected_serializing_producer_return_value == producer

            serializing_producer_mock.assert_called_once()
            expected_getenv_mock_calls: list = [
                call("KAFKA_BROKER_NAME"),
                call("KAFKA_BROKER_PORT"),
                call("MACHINE_INSTANCE_IDENTIFIER"),
            ]
            getenv_mock.assert_has_calls(expected_getenv_mock_calls, any_order=True)
            assert 3 == getenv_mock.call_count
