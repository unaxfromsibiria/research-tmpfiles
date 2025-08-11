import os

import alembic.command
import alembic.config

from sys_data_chunks import alembic_api


def create_migration(comment: str):
    """
    Creating migration without alembic scripts.
    """
    command = alembic.command.revision
    config = alembic.config.Config()
    dir = os.path.dirname(os.path.abspath(alembic_api.__file__))
    config.set_main_option("script_location", os.path.join(dir, "alembic"))
    command(config, autogenerate=True, message=comment)


def run_migration():
    """
    Update the db scheme.
    """
    command = alembic.command.upgrade
    config = alembic.config.Config()
    dir = os.path.dirname(os.path.abspath(alembic_api.__file__))
    config.set_main_option("script_location", os.path.join(dir, "alembic"))
    command(config, revision="head")
