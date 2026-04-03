# Django Log Reader

[![CI](https://github.com/bp-ventures/django-log-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/bp-ventures/django-log-reader/actions/workflows/ci.yml)

**Django Log Reader** allows you to read &amp; download log files on the admin page.

> This is a maintained fork of [imankarimi/django-log-reader](https://github.com/imankarimi/django-log-reader) with Django 6.0 support and modern packaging (PEP 621 / uv).

> This version designed for the Linux operating system and uses Linux commands to read files faster.

<br />

## Why Django Log Reader?

- Reading files based on Linux commands speeds up the display of file content
- Search in files based on Linux commands
- Download the result of the content
- Display all files according to the pattern defined in the `settings.py`
- Simple interface
- Easy integration

For one large log file and a simple literal match, `grep -F` is a good baseline and `rg -F` is often in the same range, sometimes modestly faster. Published benchmarks show `rg` at 6.73 s vs `grep` at 9.20 s on a 13.5 GB file, while Python-based scanning can be tens to more than one hundred times slower for this kind of plain-text search. Use `grep -F` or `rg -F` for raw logfile search; keep Python for cases where you need real parsing logic.

<br />

![Django Log Reader](https://raw.githubusercontent.com/imankarimi/django-log-reader/main/screenshots/django_log_reader.png)


<br>

## How to use it

<br />

* This fork is not published on PyPI. Install directly from GitHub:

```bash
$ pip install git+https://github.com/bp-ventures/django-log-reader.git
# or with uv
$ uv add git+https://github.com/bp-ventures/django-log-reader.git
```

<br />

* Add `log_reader` application to the `INSTALLED_APPS` setting of your Django project `settings.py` file:

```python
INSTALLED_APPS = (
# ...
"log_reader.apps.LogReaderConfig",
)
```

<br />

* You can Add the following value In your `settings.py` file:

```python
# This value specifies the folder for the files. The default value is 'logs'
LOG_READER_DIR_PATH = 'logs'

# This value specifies the file extensions. The default value is '*.log'
LOG_READER_FILES_PATTERN = '*.log'

# This value specifies the default file. If there is no filter, the system reads the default file.
LOG_READER_DEFAULT_FILE = 'django.log'

# The contents of the files are separated based on this pattern.
LOG_READER_SPLIT_PATTERN = "\\n"

# This value indicates the number of lines of content in the file. Set the number of lines you want to read to this value.
LOG_READER_MAX_READ_LINES = 1000

# You can exclude files with this value.
LOG_READER_EXCLUDE_FILES = []
```

<br />

* Collect static if you are in production environment:
```bash
$ python manage.py collectstatic
```

* Clear your browser cache

<br />

## Start the app

```bash
# Set up the database
$ python manage.py makemigrations
$ python manage.py migrate

# Create the superuser
$ python manage.py createsuperuser

# Start the application (development mode)
$ python manage.py runserver # default port 8000
```

* Access the `admin` section in the browser: `http://127.0.0.1:8000/`

<br />

## Changelog

### 1.2.0
- Django 6.0 compatibility (`is_composite_pk` support)
- Fixed version detection to use `django.VERSION` tuple instead of string comparison
- Fixed `grep -m` argument splitting
- Added `pyproject.toml` for uv / PEP 621 packaging
- Removed `MANIFEST.in` (replaced by hatchling build backend)
- Added CI (GitHub Actions: tests + ruff across Python 3.10/3.12/3.13)
- Removed Python 2 leftovers (`__future__` imports, `(object)` base classes)
- Updated classifiers for Django 3.2–6.0 and Python 3.8–3.13
