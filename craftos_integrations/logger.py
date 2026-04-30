"""Logger access for the integrations package.

Returns the logger configured via configure(logger=...) when available,
otherwise a standard library logger. Modules use:

    from .logger import get_logger
    logger = get_logger(__name__)
"""
from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    from .config import ConfigStore
    if ConfigStore.logger is not None:
        return ConfigStore.logger
    lg = logging.getLogger(name)
    if not lg.handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    return lg
