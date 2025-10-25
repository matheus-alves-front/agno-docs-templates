import json
import logging
import sys
import datetime


def _ts() -> str:
    """UTC timestamp with millisecond precision."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def setup_logger(level: str = "INFO") -> logging.Logger:
    """Return a configured singleton logger for the agent."""
    logger = logging.getLogger("agnodocs")
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def jlog(logger: logging.Logger, level: str, event: str, **payload) -> None:
    """Emit a structured JSON log line."""
    record = {"ts": _ts(), "level": level.upper(), "event": event, **payload}
    msg = json.dumps(record, ensure_ascii=False)
    match level.upper():
        case "ERROR":
            logger.error(msg)
        case "WARN" | "WARNING":
            logger.warning(msg)
        case _:
            logger.info(msg)
