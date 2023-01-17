import logging
import sys


def get_logger(name: str, log_level: int) -> logging.Logger:
    formatter: logging.Formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s - %(name)s: %(message)s"
    )

    handler: logging.Handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)

    return logger
