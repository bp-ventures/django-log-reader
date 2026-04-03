# Spec: Repo Polish — 80/20 Heavy Hitters

**Date:** 2026-04-03
**Branch:** `polish/packaging-ci-precommit`
**Goal:** Three changes that make the repo look maintained and professional.

---

## 1. Consolidate packaging to pyproject.toml

**Problem:** Two packaging files with conflicting versions (pyproject.toml=1.2.0, setup.py=1.1.9). Metadata (classifiers, URLs, author) only lives in setup.py.

**Changes:**

### pyproject.toml — add missing metadata

```toml
[project]
name = "django-log-reader"
version = "1.2.0"
description = "Read & Download log files on the admin page"
readme = "README.md"
license = "MIT"
requires-python = ">=3.8"
dependencies = ["django>=3.2"]
authors = [
    { name = "Iman Karimi", email = "imankarimi.mail@gmail.com" },
]
classifiers = [
    "Environment :: Web Environment",
    "Framework :: Django",
    "Framework :: Django :: 3.2",
    "Framework :: Django :: 4.0",
    "Framework :: Django :: 4.1",
    "Framework :: Django :: 4.2",
    "Framework :: Django :: 5.0",
    "Framework :: Django :: 5.1",
    "Framework :: Django :: 5.2",
    "Framework :: Django :: 6.0",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development",
]

[project.urls]
Homepage = "https://github.com/bp-ventures/django-log-reader"
```

### hatch — include templates and static files

```toml
[tool.hatch.build.targets.wheel]
packages = ["log_reader"]
```

Hatchling auto-includes non-Python files inside listed packages, so templates/ and static/ are covered in the wheel. No custom sdist `include` rule — hatchling's default sdist already includes `pyproject.toml`, `README.md`, `LICENSE`, and the packages listed above. Restricting sdist with `include = ["log_reader/**"]` would drop `README.md` (referenced by `readme = "README.md"`) and break metadata.

### Delete

- `setup.py` — no longer needed
- `MANIFEST.in` — not present, nothing to do

---

## 2. Pre-commit + ruff rules

**Problem:** No commit-time quality gate. Ruff config is bare (`line-length` only).

**Changes:**

### .pre-commit-config.yaml (new file)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### pyproject.toml — expand ruff config

```toml
[tool.ruff]
line-length = 180
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
# E/F/W = pycodestyle + pyflakes (baseline)
# I      = isort (import sorting)
# UP     = pyupgrade (modern Python idioms)
# B      = bugbear (common pitfalls)
# SIM    = simplify (unnecessary complexity)

[tool.ruff.lint.isort]
known-first-party = ["log_reader"]
```

### Add pre-commit to dev deps

```toml
[dependency-groups]
dev = ["ruff", "pre-commit"]
```

---

## 3. Django version matrix in CI

**Problem:** CI tests 3 Python versions but only one implicit Django version. README claims Django 3.2–6.0 support — CI should prove it.

**Changes to `.github/workflows/ci.yml`:**

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv python install 3.13
      - run: uv sync --dev
      - run: uv run ruff check log_reader/
      - run: uv run ruff format --check log_reader/

  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        include:
          - python-version: "3.10"
            django-version: "3.2"
          - python-version: "3.10"
            django-version: "4.2"
          - python-version: "3.12"
            django-version: "5.2"
          - python-version: "3.13"
            django-version: "6.0"
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv python install ${{ matrix.python-version }}
      - run: uv sync --dev
      - run: uv pip install "django==${{ matrix.django-version }}.*"
      - run: DJANGO_SETTINGS_MODULE=log_reader.tests.settings uv run python -m django test log_reader.tests

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv python install 3.13
      - run: uv build
      - run: uv pip install dist/*.whl
      - run: python -c "import log_reader; print(log_reader.__name__)"
```

The `build` job validates that the packaging changes actually produce a working wheel. This is the riskiest part of dropping setup.py — test it in CI, not in production.

This covers the LTS/current boundaries: 3.2 (legacy floor), 4.2 (current LTS), 5.2 (prior series to 6.0), 6.0 (latest). Lint is split to its own job so it runs once, not 4x.

---

## Files touched

| File | Action |
|------|--------|
| `pyproject.toml` | Edit — add metadata, expand ruff config, add pre-commit dep |
| `setup.py` | Delete |
| `.pre-commit-config.yaml` | Create |
| `.github/workflows/ci.yml` | Edit — split lint job, add Django matrix |

## Out of scope

- Type hints, CHANGELOG, CONTRIBUTING — separate specs if wanted
- PyPI publishing
- Coverage reporting
