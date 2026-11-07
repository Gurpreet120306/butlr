
import logging

from app.core.config import settings


def setup_logger():
    """Configure BUTL-R application logging."""

    settings.initialize_directories()

    log_file = settings.LOG_DIR / "butlr.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    logger = logging.getLogger("BUTL-R")

    logger.info("BUTL-R logging system initialized.")

    return logger
