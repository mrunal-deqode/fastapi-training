
import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from middleware import RequestIdFilter


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)

    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
