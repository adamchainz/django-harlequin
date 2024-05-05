from __future__ import annotations

import subprocess
from functools import partial
from unittest import mock

import pytest
from django.core.management.base import CommandError
from django.db import connection
from django.db.utils import ConnectionHandler
from django.test import SimpleTestCase

from django_harlequin.management.commands import harlequin as harlequin_command
from tests.utils import run_command


class CreateMaxMigrationFilesTests(SimpleTestCase):

    call_command = partial(run_command, "harlequin")

    def setUp(self):
        run_mocker = mock.patch.object(subprocess, "run")
        self.run_mock = run_mocker.start()
        self.addCleanup(run_mocker.stop)

    def test_non_existent_database(self):
        with pytest.raises(CommandError) as excinfo:
            self.call_command("--database", "nonexistent")

        assert excinfo.value.args[0] == (
            "Error: argument --database: invalid choice: 'nonexistent' "
            + "(choose from 'default')"
        )

    def test_unsupported_vendor(self):
        with mock.patch.object(connection, "vendor", new="novel"):
            with pytest.raises(CommandError) as excinfo:
                self.call_command()

        assert (
            excinfo.value.args[0]
            == "Connection 'default' has unsupported vendor 'novel'."
        )

    @mock.patch.object(
        harlequin_command,
        "connections",
        ConnectionHandler(
            {
                "default": {
                    "NAME": "example.db",
                    "ENGINE": "django.db.backends.sqlite3",
                }
            }
        ),
    )
    def test_sqlite(self):
        self.call_command()

        assert self.run_mock.mock_calls == [
            mock.call(
                ["harlequin", "-a", "sqlite", "example.db"], check=True, env=mock.ANY
            ),
        ]

    @mock.patch.object(
        harlequin_command,
        "connections",
        ConnectionHandler(
            {
                "default": {
                    "NAME": "exampledb",
                    "USER": "user",
                    "PASSWORD": "password123",
                    "HOST": "localhost",
                    "PORT": "5433",
                    "ENGINE": "django.db.backends.postgresql",
                    "OPTIONS": {},
                }
            }
        ),
    )
    def test_postgres(self):
        self.call_command()

        assert self.run_mock.mock_calls == [
            mock.call(
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
                check=True,
                env=mock.ANY,
            ),
        ]
        assert self.run_mock.mock_calls[0].kwargs["env"]["PGPASSWORD"] == "password123"
