from __future__ import annotations

import os
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
        execvpe_mocker = mock.patch.object(os, "execvpe")
        self.execvpe_mock = execvpe_mocker.start()
        self.addCleanup(execvpe_mocker.stop)

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
        self.call_command()

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
        self.call_command()

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
        self.call_command()

        assert self.execvpe_mock.mock_calls == [
            mock.call(
                "harlequin",
                ["harlequin", "-a", "sqlite", "example.db"],
                env=mock.ANY,
            ),
        ]
