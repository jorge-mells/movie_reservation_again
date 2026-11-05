import logging
import logging.config
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def setup_logging(debug: bool = False) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": RequestIDFilter}},
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
                },
                "console": {
                    "format": "%(asctime)s | %(levelname)-8s | %(message)s | rid=%(request_id)s",
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "console" if debug else "json",
                    "filters": ["request_id"],
                },
            },
            "root": {"level": "INFO", "handlers": ["stdout"]},
            "loggers": {
                "uvicorn": {"level": "INFO", "propagate": True},
                "uvicorn.access": {"level": "INFO", "propagate": True},
                "uvicorn.error": {"level": "INFO", "propagate": True},
            },
        }
    )
