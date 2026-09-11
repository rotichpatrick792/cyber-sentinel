import logging
import sys

from app.core.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    """Configure the root logger for the whole application."""
    level = logging.DEBUG if settings.debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.handlers.append(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use this everywhere instead of print()."""
    return logging.getLogger(name)
