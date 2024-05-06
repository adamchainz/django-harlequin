from __future__ import annotations

import os
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
        if connection.vendor == "mysql":
            self.extend_command_env_mysql(connection, command, env)
        elif connection.vendor == "postgresql":
            self.extend_command_env_postgres(connection, command, env)
        elif connection.vendor == "sqlite":
            self.extend_command_env_sqlite(connection, command, env)
        else:
            raise CommandError(
                f"Connection {database!r} has unsupported vendor {connection.vendor!r}."
            )

        # Pass through extra options
        command.extend(parameters)
        env = {**os.environ, **env}
        os.execvpe(command[0], command, env=env)

    def extend_command_env_mysql(
        self, connection: BaseDatabaseWrapper, command: list[str], env: dict[str, str]
    ) -> None:
        command.extend(["-a", "mysql"])

        settings_dict = connection.settings_dict
        database = settings_dict["OPTIONS"].get(
            "database",
            settings_dict["OPTIONS"].get("db", settings_dict["NAME"]),
        )
        user = settings_dict["OPTIONS"].get("user", settings_dict["USER"])
        password = settings_dict["OPTIONS"].get(
            "password",
            settings_dict["OPTIONS"].get("passwd", settings_dict["PASSWORD"]),
        )
        host = settings_dict["OPTIONS"].get("host", settings_dict["HOST"])
        port = settings_dict["OPTIONS"].get("port", settings_dict["PORT"])
        server_ca = settings_dict["OPTIONS"].get("ssl", {}).get("ca")
        client_cert = settings_dict["OPTIONS"].get("ssl", {}).get("cert")
        client_key = settings_dict["OPTIONS"].get("ssl", {}).get("key")

        if database:  # pragma: no branch
            command += ["--database", database]
        if user:  # pragma: no branch
            command += ["--user", user]
        if password:  # pragma: no branch
            # Django’s dbshell uses the MYSQL_PWD environment variable as a
            # slightly more secure way of passing the password, but Harlequin
            # uses mysql-connector-python which doesn’t seem to read this
            # variable. Thus we have to use --password.
            command += ["--password", password]
        if host:  # pragma: no branch
            command += ["--host", host]
        if port:  # pragma: no branch
            command += ["--port", port]
        if server_ca:  # pragma: no cover
            command += ["--ssl-ca", server_ca]
        if client_cert:  # pragma: no cover
            command += ["--ssl-cert", client_cert]
        if client_key:  # pragma: no cover
            command += ["--ssl-key", client_key]

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

    def extend_command_env_sqlite(
        self, connection: BaseDatabaseWrapper, command: list[str], env: dict[str, str]
    ) -> None:
        command.extend(
            [
                "-a",
                "sqlite",
                connection.settings_dict["NAME"],
            ]
        )
