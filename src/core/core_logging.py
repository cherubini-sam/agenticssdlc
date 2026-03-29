"""Structured JSON logs on Cloud Run, human-readable locally."""

import json
import logging
import os

from src.core.core_utils import (
    CORE_LOGGING_CONSOLE_DATE_FORMAT,
    CORE_LOGGING_CONSOLE_FORMAT,
    CORE_LOGGING_DEFAULT_LOG_LEVEL,
    CORE_LOGGING_JSON_KEY_EXCEPTION,
    CORE_LOGGING_JSON_KEY_LOGGER,
    CORE_LOGGING_JSON_KEY_MESSAGE,
    CORE_LOGGING_JSON_KEY_SEVERITY,
    CORE_LOGGING_JSON_KEY_TIMESTAMP,
    CORE_LOGGING_JSON_TIMESTAMP_FORMAT,
    CORE_LOGGING_K_SERVICE_ENV,
    CORE_LOGGING_NOISY_LOGGERS,
)


def core_logging_setup_logging(log_level: str = CORE_LOGGING_DEFAULT_LOG_LEVEL) -> None:
    """Wire up logging. Picks JSON or console format based on K_SERVICE env var."""

    level = getattr(logging, log_level.upper(), logging.INFO)

    if os.environ.get(CORE_LOGGING_K_SERVICE_ENV):
        # Running on Cloud Run — emit JSON that Cloud Logging parses natively
        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_entry = {
                    CORE_LOGGING_JSON_KEY_SEVERITY: record.levelname,
                    CORE_LOGGING_JSON_KEY_MESSAGE: record.getMessage(),
                    CORE_LOGGING_JSON_KEY_TIMESTAMP: self.formatTime(
                        record, CORE_LOGGING_JSON_TIMESTAMP_FORMAT
                    ),
                    CORE_LOGGING_JSON_KEY_LOGGER: record.name,
                }
                if record.exc_info:
                    log_entry[CORE_LOGGING_JSON_KEY_EXCEPTION] = self.formatException(
                        record.exc_info
                    )
                return json.dumps(log_entry)

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt=CORE_LOGGING_CONSOLE_FORMAT,
                datefmt=CORE_LOGGING_CONSOLE_DATE_FORMAT,
            )
        )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    for noisy in CORE_LOGGING_NOISY_LOGGERS:
        logging.getLogger(noisy).setLevel(logging.WARNING)
