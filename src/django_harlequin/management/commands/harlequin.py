from __future__ import annotations

import os
import subprocess
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                'Nominates a database to synchronize. Defaults to the "default" '
                "database."
            ),
        )
        parameters = parser.add_argument_group("parameters", prefix_chars="--")
        parameters.add_argument("parameters", nargs="*")

    def handle(self, *args: Any, **options: Any) -> None:
        database: str = options["database"]
        parameters: list[str] = options["parameters"]

        command = ["harlequin"]
        env: dict[str, str] = {}

        connection = connections[database]
        if connection.vendor == "postgresql":
            self.extend_command_env_postgres(connection, command, env)
        else:
            raise CommandError(
                f"Connection {database!r} has unsupported vendor {connection.vendor!r}."
            )

        # Pass through extra options
        command.extend(parameters)
        env_arg = {**os.environ, **env} if env else None
        subprocess.run(command, check=True, env=env_arg)

    def extend_command_env_postgres(
        self, connection: BaseDatabaseWrapper, command: list[str], env: dict[str, str]
    ) -> None:
        command.extend(["-a", "postgres"])

        options = connection.settings_dict["OPTIONS"]

        host = connection.settings_dict.get("HOST")
        port = connection.settings_dict.get("PORT")
        dbname = connection.settings_dict.get("NAME")
        user = connection.settings_dict.get("USER")
        passwd = connection.settings_dict.get("PASSWORD")
        passfile = options.get("passfile")
        service = options.get("service")
        sslmode = options.get("sslmode")
        sslrootcert = options.get("sslrootcert")
        sslcert = options.get("sslcert")
        sslkey = options.get("sslkey")

        if not dbname and not service:  # pragma: no cover
            # Connect to the default 'postgres' db.
            dbname = "postgres"
        if user:  # pragma: no branch
            command += ["--user", user]
        if host:  # pragma: no branch
            command += ["--host", host]
        if port:  # pragma: no branch
            command += ["--port", str(port)]
        if dbname:  # pragma: no branch
            command += ["--dbname", dbname]

        if passwd:
            env["PGPASSWORD"] = str(passwd)
        if service:  # pragma: no cover
            env["PGSERVICE"] = str(service)
        if sslmode:  # pragma: no cover
            env["PGSSLMODE"] = str(sslmode)
        if sslrootcert:  # pragma: no cover
            env["PGSSLROOTCERT"] = str(sslrootcert)
        if sslcert:  # pragma: no cover
            env["PGSSLCERT"] = str(sslcert)
        if sslkey:  # pragma: no cover
            env["PGSSLKEY"] = str(sslkey)
        if passfile:  # pragma: no cover
            env["PGPASSFILE"] = str(passfile)
