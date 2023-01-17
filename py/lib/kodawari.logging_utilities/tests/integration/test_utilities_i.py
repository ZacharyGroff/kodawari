import logging

from logging_utilities.utilities import get_logger


def test_get_logger_logs(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    log_message: str = "test"
    logger: logging.Logger = get_logger(__name__, logging.DEBUG)
    logger.debug(log_message)

    result_split: list[str] = caplog.text.split()

    assert result_split[0] == "DEBUG"
    assert __name__ in result_split[1]
    assert result_split[2] == log_message


def test_get_logger_does_not_log_when_set_level_is_too_low(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    log_message: str = "this_should_not_be_logged"
    logger: logging.Logger = get_logger(__name__, logging.ERROR)
    logger.debug(log_message)

    assert "DEBUG" not in caplog.text
    assert __name__ not in caplog.text
    assert log_message not in caplog.text
