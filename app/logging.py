"""Logging helpers using loguru."""
from __future__ import annotations

import sys
from loguru import logger

from .config import settings


def configure_logging() -> None:
    """Configure loguru once for the entire app."""

    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        enqueue=True,
        colorize=False,
        backtrace=False,
        diagnose=False,
    )


configure_logging()
