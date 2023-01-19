import logging
import sys
from typing import List
from unittest.mock import patch

from logging_utilities.utilities import get_logger


class MockHandler(logging.Handler):
    set_level_called_times: int = 0
    set_level_called_with: List[int] = []
    set_formatter_called_times: int = 0
    set_formatter_called_with: List[logging.Formatter] = []

    def setLevel(self, level: int):
        self.set_level_called_with.append(level)
        self.set_level_called_times += 1

    def setFormatter(self, formatter: logging.Formatter):
        self.set_formatter_called_with.append(formatter)
        self.set_formatter_called_times += 1


class MockLogger(logging.Logger):
    set_level_called_times: int = 0
    set_level_called_with: List[int] = []
    add_handler_called_times: int = 0
    add_handler_called_with: List[logging.Handler] = []

    def setLevel(self, level: int):
        self.set_level_called_with.append(level)
        self.set_level_called_times += 1

    def addHandler(self, handler: logging.Handler):
        self.add_handler_called_with.append(handler)
        self.add_handler_called_times += 1


def test_get_logger() -> None:
    expected_name: str = "my-test-name"
    expected_log_level: int = logging.DEBUG
    expected_formatter: logging.Formatter = logging.Formatter()
    expected_handler: logging.Handler = MockHandler()
    expected_logger: logging.Logger = MockLogger(expected_name)

    with patch("logging_utilities.utilities.logging.Formatter") as formatter_mock:
        with patch(
            "logging_utilities.utilities.logging.StreamHandler"
        ) as stream_handler_mock:

            with patch(
                "logging_utilities.utilities.logging.getLogger"
            ) as get_logger_mock:
                formatter_mock.return_value = expected_formatter
                stream_handler_mock.return_value = expected_handler
                get_logger_mock.return_value = expected_logger

                actual_logger: logging.Logger = get_logger(
                    expected_name, expected_log_level
                )

                assert expected_logger == actual_logger

                assert expected_handler.set_level_called_times == 1
                assert expected_handler.set_level_called_with[0] == expected_log_level
                assert expected_handler.set_formatter_called_times == 1
                assert (
                    expected_handler.set_formatter_called_with[0] == expected_formatter
                )

                assert expected_logger.set_level_called_times == 1
                assert expected_logger.set_level_called_with[0] == expected_log_level
                assert expected_logger.add_handler_called_times == 1
                assert expected_logger.add_handler_called_with[0] == expected_handler

                formatter_mock.assert_called_once_with(
                    "[%(levelname)s] %(asctime)s - %(name)s: %(message)s"
                )
                stream_handler_mock.assert_called_once_with(sys.stdout)
                get_logger_mock.assert_called_once_with(expected_name)
