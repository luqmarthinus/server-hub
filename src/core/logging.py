import sys
from typing import Any, Dict

from loguru import logger

from src.core.config import settings


def configure_logging() -> None:
    logger.remove()

    log_level = settings.LOG_LEVEL

    if settings.ENVIRONMENT == "development":
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            enqueue=True,
        )
    else:
        def json_formatter(record: Dict[str, Any]) -> str:
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "logger": record["name"],
                "message": record["message"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            }
            if record.get("extra"):
                log_entry["extra"] = record["extra"]
            return f"{__import__('json').dumps(log_entry)}\n"

        logger.add(
            sys.stderr,
            format=json_formatter,
            level=log_level,
            enqueue=True,
        )

    logger.info(f"Logging configured. Environment: {settings.ENVIRONMENT}, Level: {log_level}")


def get_logger(name: str = None):
    if name:
        return logger.bind(name=name)
    return logger
