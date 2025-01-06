from __future__ import annotations

import os
import sys
from functools import partial
from inspect import getsource
from textwrap import dedent
from unittest import mock

import django
import pytest
from django.core.management.base import CommandError
from django.db import connection
from django.db.utils import ConnectionHandler
from django.test import SimpleTestCase

from django_harlequin.management.commands import harlequin as harlequin_command
from tests.utils import run_command

call_command = partial(run_command, "harlequin")


class HarlequinTests(SimpleTestCase):

    def setUp(self):
        execvpe_mocker = mock.patch.object(os, "execvpe")
        self.execvpe_mock = execvpe_mocker.start()
        self.addCleanup(execvpe_mocker.stop)

    def test_non_existent_database(self):
        with pytest.raises(CommandError) as excinfo:
            call_command("--database", "nonexistent")

        if (sys.version_info[:2] == (3, 12) and sys.version_info >= (3, 12, 8)) or (
            sys.version_info >= (3, 13) and sys.version_info >= (3, 13, 1)
        ):
            # CPython change:
            # gh-117766: Always use str() to print choices in argparse.
            assert excinfo.value.args[0] == (
                "Error: argument --database: invalid choice: 'nonexistent' "
                + "(choose from default)"
            )
        else:
            assert excinfo.value.args[0] == (
                "Error: argument --database: invalid choice: 'nonexistent' "
                + "(choose from 'default')"
            )

    def test_unsupported_vendor(self):
        with mock.patch.object(connection, "vendor", new="novel"):
            with pytest.raises(CommandError) as excinfo:
                call_command()

        assert (
            excinfo.value.args[0]
            == "Connection 'default' has unsupported vendor 'novel'."
        )

    @pytest.mark.skipif(django.VERSION < (5, 1), reason="Django 5.1+ version expected.")
    def test_upstream_dbshell_expected_source(self):
        """
        Monitor this upstream command for relevant changes.
        """
        from django.core.management.commands import dbshell

        source = getsource(dbshell)
        expected = dedent(
            """\
            import subprocess

            from django.core.management.base import BaseCommand, CommandError
            from django.db import DEFAULT_DB_ALIAS, connections


            class Command(BaseCommand):
                help = (
                    "Runs the command-line client for specified database, or the "
                    "default database if none is provided."
                )

                requires_system_checks = []

                def add_arguments(self, parser):
                    parser.add_argument(
                        "--database",
                        default=DEFAULT_DB_ALIAS,
                        choices=tuple(connections),
                        help=(
                            "Nominates a database onto which to open a shell. Defaults to the "
                            '"default" database.'
                        ),
                    )
                    parameters = parser.add_argument_group("parameters", prefix_chars="--")
                    parameters.add_argument("parameters", nargs="*")

                def handle(self, **options):
                    connection = connections[options["database"]]
                    try:
                        connection.client.runshell(options["parameters"])
                    except FileNotFoundError:
                        # Note that we're assuming the FileNotFoundError relates to the
                        # command missing. It could be raised for some other reason, in
                        # which case this error message would be inaccurate. Still, this
                        # message catches the common case.
                        raise CommandError(
                            "You appear not to have the %r program installed or on your path."
                            % connection.client.executable_name
                        )
                    except subprocess.CalledProcessError as e:
                        raise CommandError(
                            '"%s" returned non-zero exit status %s.'
                            % (
                                " ".join(map(str, e.cmd)),
                                e.returncode,
                            ),
                            returncode=e.returncode,
                        )
            """
        )
        assert source == expected

    @pytest.mark.skipif(django.VERSION < (5, 0), reason="Django 5.0+ version expected.")
    def test_upstream_client_expected_source(self):
        """
        Monitor this upstream client for relevant changes.
        """
        from django.db.backends.base import client

        source = getsource(client)
        expected = dedent(
            '''\
            import os
            import subprocess


            class BaseDatabaseClient:
                """Encapsulate backend-specific methods for opening a client shell."""

                # This should be a string representing the name of the executable
                # (e.g., "psql"). Subclasses must override this.
                executable_name = None

                def __init__(self, connection):
                    # connection is an instance of BaseDatabaseWrapper.
                    self.connection = connection

                @classmethod
                def settings_to_cmd_args_env(cls, settings_dict, parameters):
                    raise NotImplementedError(
                        "subclasses of BaseDatabaseClient must provide a "
                        "settings_to_cmd_args_env() method or override a runshell()."
                    )

                def runshell(self, parameters):
                    args, env = self.settings_to_cmd_args_env(
                        self.connection.settings_dict, parameters
                    )
                    env = {**os.environ, **env} if env else None
                    subprocess.run(args, env=env, check=True)
            '''
        )
        assert source == expected

    @mock.patch.object(
        harlequin_command,
        "connections",
        ConnectionHandler(
            {
                "default": {
                    "ENGINE": "django.db.backends.mysql",
                    "NAME": "exampledb",
                    "USER": "user",
                    "PASSWORD": "password123",
                    "HOST": "localhost",
                    "PORT": "3307",
                }
            }
        ),
    )
    def test_mysql(self):
        call_command()

        assert self.execvpe_mock.mock_calls == [
            mock.call(
                "harlequin",
                [
                    "harlequin",
                    "-a",
                    "mysql",
                    "--database",
                    "exampledb",
                    "--user",
                    "user",
                    "--password",
                    "password123",
                    "--host",
                    "localhost",
                    "--port",
                    "3307",
                ],
                env=mock.ANY,
            ),
        ]

    @pytest.mark.skipif(django.VERSION < (5, 0), reason="Django 5.0+ version expected.")
    def test_upstream_mysql_client_expected_source(self):
        """
        Monitor this upstream module for relevant changes.
        """
        from django.db.backends.mysql import client

        source = getsource(client)
        expected = dedent(
            """\
            import signal

            from django.db.backends.base.client import BaseDatabaseClient


            class DatabaseClient(BaseDatabaseClient):
                executable_name = "mysql"

                @classmethod
                def settings_to_cmd_args_env(cls, settings_dict, parameters):
                    args = [cls.executable_name]
                    env = None
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
                    defaults_file = settings_dict["OPTIONS"].get("read_default_file")
                    charset = settings_dict["OPTIONS"].get("charset")
                    # Seems to be no good way to set sql_mode with CLI.

                    if defaults_file:
                        args += ["--defaults-file=%s" % defaults_file]
                    if user:
                        args += ["--user=%s" % user]
                    if password:
                        # The MYSQL_PWD environment variable usage is discouraged per
                        # MySQL's documentation due to the possibility of exposure through
                        # `ps` on old Unix flavors but --password suffers from the same
                        # flaw on even more systems. Usage of an environment variable also
                        # prevents password exposure if the subprocess.run(check=True) call
                        # raises a CalledProcessError since the string representation of
                        # the latter includes all of the provided `args`.
                        env = {"MYSQL_PWD": password}
                    if host:
                        if "/" in host:
                            args += ["--socket=%s" % host]
                        else:
                            args += ["--host=%s" % host]
                    if port:
                        args += ["--port=%s" % port]
                    if server_ca:
                        args += ["--ssl-ca=%s" % server_ca]
                    if client_cert:
                        args += ["--ssl-cert=%s" % client_cert]
                    if client_key:
                        args += ["--ssl-key=%s" % client_key]
                    if charset:
                        args += ["--default-character-set=%s" % charset]
                    if database:
                        args += [database]
                    args.extend(parameters)
                    return args, env

                def runshell(self, parameters):
                    sigint_handler = signal.getsignal(signal.SIGINT)
                    try:
                        # Allow SIGINT to pass to mysql to abort queries.
                        signal.signal(signal.SIGINT, signal.SIG_IGN)
                        super().runshell(parameters)
                    finally:
                        # Restore the original SIGINT handler.
                        signal.signal(signal.SIGINT, sigint_handler)
            """
        )
        assert source == expected

    @mock.patch.object(
        harlequin_command,
        "connections",
        ConnectionHandler(
            {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "HOST": "localhost",
                    "NAME": "exampledb",
                    "OPTIONS": {},
                    "PASSWORD": "password123",
                    "PORT": "5433",
                    "USER": "user",
                }
            }
        ),
    )
    def test_postgres(self):
        call_command()

        assert self.execvpe_mock.mock_calls == [
            mock.call(
                "harlequin",
                [
                    "harlequin",
                    "-a",
                    "postgres",
                    "--user",
                    "user",
                    "--host",
                    "localhost",
                    "--port",
                    "5433",
                    "--dbname",
                    "exampledb",
                ],
                env=mock.ANY,
            ),
        ]
        assert (
            self.execvpe_mock.mock_calls[0].kwargs["env"]["PGPASSWORD"] == "password123"
        )

    @pytest.mark.skipif(django.VERSION < (5, 1), reason="Django 5.1+ version expected.")
    def test_upstream_postgres_client_expected_source(self):
        """
        Monitor this upstream module for relevant changes.
        """
        from django.db.backends.postgresql import client

        source = getsource(client)
        expected = dedent(
            """\
            import signal

            from django.db.backends.base.client import BaseDatabaseClient


            class DatabaseClient(BaseDatabaseClient):
                executable_name = "psql"

                @classmethod
                def settings_to_cmd_args_env(cls, settings_dict, parameters):
                    args = [cls.executable_name]
                    options = settings_dict["OPTIONS"]

                    host = settings_dict.get("HOST")
                    port = settings_dict.get("PORT")
                    dbname = settings_dict.get("NAME")
                    user = settings_dict.get("USER")
                    passwd = settings_dict.get("PASSWORD")
                    passfile = options.get("passfile")
                    service = options.get("service")
                    sslmode = options.get("sslmode")
                    sslrootcert = options.get("sslrootcert")
                    sslcert = options.get("sslcert")
                    sslkey = options.get("sslkey")

                    if not dbname and not service:
                        # Connect to the default 'postgres' db.
                        dbname = "postgres"
                    if user:
                        args += ["-U", user]
                    if host:
                        args += ["-h", host]
                    if port:
                        args += ["-p", str(port)]
                    args.extend(parameters)
                    if dbname:
                        args += [dbname]

                    env = {}
                    if passwd:
                        env["PGPASSWORD"] = str(passwd)
                    if service:
                        env["PGSERVICE"] = str(service)
                    if sslmode:
                        env["PGSSLMODE"] = str(sslmode)
                    if sslrootcert:
                        env["PGSSLROOTCERT"] = str(sslrootcert)
                    if sslcert:
                        env["PGSSLCERT"] = str(sslcert)
                    if sslkey:
                        env["PGSSLKEY"] = str(sslkey)
                    if passfile:
                        env["PGPASSFILE"] = str(passfile)
                    return args, (env or None)

                def runshell(self, parameters):
                    sigint_handler = signal.getsignal(signal.SIGINT)
                    try:
                        # Allow SIGINT to pass to psql to abort queries.
                        signal.signal(signal.SIGINT, signal.SIG_IGN)
                        super().runshell(parameters)
                    finally:
                        # Restore the original SIGINT handler.
                        signal.signal(signal.SIGINT, sigint_handler)
            """
        )
        assert source == expected

    @mock.patch.object(
        harlequin_command,
        "connections",
        ConnectionHandler(
            {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "example.db",
                }
            }
        ),
    )
    def test_sqlite(self):
        call_command()

        assert self.execvpe_mock.mock_calls == [
            mock.call(
                "harlequin",
                ["harlequin", "-a", "sqlite", "example.db"],
                env=mock.ANY,
            ),
        ]

    @pytest.mark.skipif(django.VERSION < (5, 0), reason="Django 5.0+ version expected.")
    def test_upstream_sqlite_client_expected_source(self):
        """
        Monitor this upstream module for relevant changes.
        """
        from django.db.backends.sqlite3 import client

        source = getsource(client)
        expected = dedent(
            """\
            from django.db.backends.base.client import BaseDatabaseClient


            class DatabaseClient(BaseDatabaseClient):
                executable_name = "sqlite3"

                @classmethod
                def settings_to_cmd_args_env(cls, settings_dict, parameters):
                    args = [cls.executable_name, settings_dict["NAME"], *parameters]
                    return args, None
            """
        )
        assert source == expected
