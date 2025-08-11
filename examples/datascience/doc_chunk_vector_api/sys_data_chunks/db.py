import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.engine.url import make_url

from sys_data_chunks.settings import ServerSettings

db_access: Optional[Engine] = None


def connection_url(settings: ServerSettings) -> URL:
    """
    Db connection configuration.
    Configuration source is the environment variables
    instead of configuration files or something.
    postgresql+psycopg2://user:password@host:port/dbname
    """
    return make_url(settings.db_connection)


def current_engine(settings: Optional[ServerSettings] = None) -> Engine:
    """
    Get or init db engine (lazy initialization of connection).
    """
    global db_access
    if db_access is None:
        if settings is None:
            settings = ServerSettings()

        conn_str = connection_url(settings=settings)
        db_access = create_engine(conn_str, echo=settings.sql_debug)
        logger = logging.getLogger("sqlalchemy.engine")
        logger.info("New db connection: %s", conn_str)
        if not settings.debug_use:
            logger.setLevel(logging.WARNING)

    return db_access
