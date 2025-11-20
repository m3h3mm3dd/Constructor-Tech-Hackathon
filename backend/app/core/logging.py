"""
Logging configuration for the AI agent backend.

This module configures Python's built-in logging library to emit log
messages in a consistent format. It's useful to call ``setup_logging()``
at application startup so that all imported modules use the same log
configuration. You can modify the formatting, log levels, or add
handlers to integrate with structured logging solutions.
"""

import logging


def setup_logging() -> None:
    """Configure root logger with a basic format and INFO level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )