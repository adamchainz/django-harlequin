================
django-harlequin
================

.. image:: https://img.shields.io/github/actions/workflow/status/adamchainz/django-harlequin/main.yml.svg?branch=main&style=for-the-badge
   :target: https://github.com/adamchainz/django-harlequin/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
   :target: https://github.com/adamchainz/django-harlequin/actions?workflow=CI

.. image:: https://img.shields.io/pypi/v/django-harlequin.svg?style=for-the-badge
   :target: https://pypi.org/project/django-harlequin/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Launch `Harlequin <https://harlequin.sh/>`__, the SQL IDE for your Terminal, with your Django database configuration.

----

**Work smarter and faster** with my book `Boost Your Django DX <https://adamchainz.gumroad.com/l/byddx>`__ which covers many tools to improve your development experience.

----

Requirements
============

Python 3.9 to 3.13 supported.

Django 3.2 to 5.1 supported.

Supported database backends: MariaDB/MySQL, PostgreSQL, SQLite.

Installation
============

**First,** install with pip:

.. code-block:: bash

    python -m pip install django-harlequin

**Second,** install Harlequin with appropriate Harlequin `adapter packages <https://harlequin.sh/docs/adapters>`__ for the database backends you use.
For example, to install Harlequin with the `PostgreSQL adapter <https://harlequin.sh/docs/postgres/index>`__:

.. code-block:: bash

    python -m pip install 'harlequin[postgres]'

Harlequin does not need to be installed in the same virtual environment as Django, as django-harlequin does not import it.
You only need the ``harlequin`` command on your path, so you can install Harlequin globally, or in an isolated virtual environment with a tool like `pipx <https://pipx.pypa.io/latest/installation/>`__.

**Third,** add the app to your ``INSTALLED_APPS`` setting:

.. code-block:: python

    INSTALLED_APPS = [
        ...,
        "django_harlequin",
        ...,
    ]

Usage
=====

``harlequin`` command
---------------------

Run the ``harlequin`` management command to launch Harlequin, connected to your default database:

.. code-block:: console

    $ ./manage.py harlequin

Pass ``--database`` to select a different database connection from ``settings.DATABASES``:

.. code-block:: console

    $ ./manage.py harlequin --database replica

Extra options, optionally after a ``--`` delimiter, will be passed through to Harlequin.
For example, to read its help page, as opposed to that of the management command:

.. code-block:: console

    $ ./manage.py harlequin -- --help

Configuration
=============

Harlequin automatically loads configuration from ``pyproject.toml`` or its own files within the current working directory, which would mean next to your ``manage.py`` file.
See Harlequin’s `configuration documentation <https://harlequin.sh/docs/config-file>`__ for details on the available options.
