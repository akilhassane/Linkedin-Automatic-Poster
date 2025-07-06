import logging
from logging.handlers import RotatingFileHandler
import os


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "app.log")


def init_logging():
    """Configure root logger with console & rotating file handler."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # Already configured
        return

    root_logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    # Rotating file handler (5 files × 2 MB)
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=5)
    fh.setLevel(LOG_LEVEL)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    root_logger.debug("Logging initialised – level=%s, file=%s", LOG_LEVEL, LOG_FILE)