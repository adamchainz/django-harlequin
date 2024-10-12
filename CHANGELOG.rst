=========
Changelog
=========

1.3.0 (2024-10-12)
------------------

* Drop Python 3.8 support.

* Support Python 3.13.

1.2.0 (2024-06-19)
------------------

* Support Django 5.1.

1.1.2 (2024-05-10)
------------------

* Remove the dependency on Harlequin.
  This allows you to use a global install, or an isolated one with a tool like pipx.

1.1.1 (2024-05-08)
------------------

* Declare a dependency on Harlequin so it is installed along with this package.

1.1.0 (2024-05-06)
------------------

* Use ``os.execvpe()`` to launch Harlequin, which replaces the Django process, reducing overall memory usage.

1.0.0 (2024-05-05)
------------------

* Initial release.
