"""
Logging configuration for IFOps CLI.
"""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from ..core.config import load_config


def setup_logging(level: Optional[str] = None) -> None:
    """Setup logging configuration."""
    config = load_config()
    log_level = level or config["logging"]["level"]

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_path=False,
                markup=True
            )
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
