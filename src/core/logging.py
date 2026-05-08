"""
Loguru logging configuration with optional JSON output for Loki.
"""

import sys

from loguru import logger

from src.core.config import settings


def configure_logging() -> None:
    """Configure Loguru with console output (pretty for dev, JSON for testing/production)."""
    logger.remove()  # Remove default handler

    log_level = settings.LOG_LEVEL

    if settings.ENVIRONMENT == "development":
        # Human-readable console output for dev
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",  # noqa: E501
            level=log_level,
            enqueue=True,
        )
    else:
        # JSON output for testing/production (Loki-friendly)
        logger.add(
            sys.stderr,
            serialize=True,
            level=log_level,
            enqueue=True,
        )

    logger.info(f"Logging configured. Environment: {settings.ENVIRONMENT}, Level: {log_level}")


def get_logger(name: str = None):
    """Return a logger optionally bound to a name."""
    if name:
        return logger.bind(name=name)
    return logger
