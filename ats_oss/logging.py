import logging
import sys
from ats_oss.config import settings

def get_logger(name: str):
    """
    Creates and configures a logger instance.
    """
    logger = logging.getLogger(name)

    # Set the level from the config.
    log_level = getattr(logging, settings.logging_level, logging.INFO)
    logger.setLevel(log_level)

    # If the logger already has handlers, don't add more.
    # This prevents duplicate log messages if the function is called multiple times.
    if logger.hasHandlers():
        return logger

    # Create a handler to write log messages to the console (stderr)
    handler = logging.StreamHandler(sys.stderr)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger

# You can also create a default logger for the application
log = get_logger("ats_oss")
