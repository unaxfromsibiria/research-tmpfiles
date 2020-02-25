import logging
import os
from dotenv import load_dotenv
import sys

DEFAULT_LOGGERNAME: str = "common"
BASE_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_PATH, "dev-app.env"))


def env_var_line(key: str) -> str:
    """Reading a environment variable as text.
    """
    return str(os.environ.get(key) or "").strip()


def env_var_int(key: str) -> int:
    """Reading a environment variable as int.
    """
    try:
        return int(env_var_line(key))
    except (ValueError, TypeError):
        return 0


def env_var_float(key: str) -> float:
    """Reading a environment variable as float.
    """
    try:
        return float(env_var_line(key))
    except (ValueError, TypeError):
        return 0


def env_var_bool(key: str) -> bool:
    """Reading a environment variable as binary.
    """
    return env_var_line(key).upper() in ("TRUE", "ON", "YES")


def env_var_list(key: str) -> list:
    """Reading a environment variable as list,
    source line should be divided by commas.
    """
    return list(
        filter(
            None, map(str.strip, env_var_line(key).split(","))
        )
    )


logger = logging.getLogger(DEFAULT_LOGGERNAME)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(getattr(logging, env_var_line("LOGLEVEL") or "INFO"))
