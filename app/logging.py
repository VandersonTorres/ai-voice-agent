import logging
import sys

from .config import LOG_LEVEL

# Configure root logger
logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger with the specified name (or root if None)"""
    return logging.getLogger(name)
