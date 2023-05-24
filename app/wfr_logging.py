"""Logging setup."""
from datetime import datetime
import logging
from typing import Optional
import uuid



class TRAPILogEntryFormatter(logging.Formatter):
    """Format to match TRAPI LogEntry."""

    def format(self, record):
        log_entry = {}

        # If given a string use that as the message
        if isinstance(record.msg, str):
            log_entry["message"] = record.msg

        # If given a dict, just use that as the log entry
        # Make sure everything is serializeable
        if isinstance(record.msg, dict):
            log_entry |= record.msg

        # Add timestamp
        iso_timestamp = datetime.utcfromtimestamp(
            record.created
        ).isoformat()
        log_entry["timestamp"] = iso_timestamp

        # Add level
        log_entry["level"] = record.levelname

        return log_entry


class ListLogHandler(logging.Handler):
    """List log handler."""

    def __init__(self, **kwargs):
        self.store = []
        super().__init__(**kwargs)

    def emit(self, record):
        log_entry = self.format(record)
        self.store.append(log_entry)


def gen_logger(name: Optional[str] = None, **kwargs):
    if name is None:
        name = str(uuid.uuid4())
    logger = logging.getLogger(name)
    formatter = TRAPILogEntryFormatter()
    handler = ListLogHandler(**kwargs)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
