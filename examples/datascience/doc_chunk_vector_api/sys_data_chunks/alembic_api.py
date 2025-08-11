import os
import typing
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import DeclarativeMeta

from sys_data_chunks.db import ServerSettings
from sys_data_chunks.db import connection_url
from sys_data_chunks.models import BaseModel


def select_db() -> typing.Tuple[
    typing.Optional[DeclarativeMeta], URL
]:
    """
    Get db connections from app configuration.
    """
    return BaseModel, connection_url(settings=ServerSettings())


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    base, url = select_db()

    context.configure(
        url=url,
        literal_binds=True,
        compare_type=True,
        target_metadata=base.metadata
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    base, url = select_db()

    conf = context.config.get_section(context.config.config_ini_section)
    conf.update({"sqlalchemy.url": url})

    connectable = engine_from_config(
        conf, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        with connection.begin():
            context.configure(connection=connection, target_metadata=base.metadata)
            with context.begin_transaction():
                context.run_migrations()


def main_env():
    """
    Main method for env.py.
    """
    config = context.config
    script_location = config.get_main_option("script_location")
    fileConfig(f"{script_location}.ini")

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


def apply_migtarion(*args, **kwargs):
    """
    Run Alembic migrations.
    """
    from alembic import config as alembic_conf

    current_dir = os.path.dirname(os.path.abspath(__file__))

    alembic_args = [
        "-c",
        os.path.join(current_dir, "alembic.ini"),
        "upgrade",
        "head",
    ]

    alembic_conf.main(argv=alembic_args)
