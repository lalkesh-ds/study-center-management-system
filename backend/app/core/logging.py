import logging
import sys
from backend.app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configures application-wide logging.
    Emits structured, formatted logs to standard output.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=logging_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

    # Suppress verbose third-party logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("smart_library")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
