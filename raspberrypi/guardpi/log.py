import logging

from .const import LOG_FILEPATH, LOG_LEVEL, LOGGER_NAME

logger_data = {}


def init_logger(new_logger=None):
    """Prepare logging.
    """
    if new_logger:
        logger_data["logger"] = new_logger
    else:
        logging.basicConfig(
            filename=LOG_FILEPATH,
            format=(
                "%(asctime)s - %(name)s - "
                "%(levelname)s - %(message)s"),
            level=getattr(logging, LOG_LEVEL, "INFO"))
        logger_data["logger"] = logging.getLogger(LOGGER_NAME)


def get_logger():
    """Do not use logging.getLogger.
    """
    if not logger_data:
        init_logger()
    return logger_data["logger"]
