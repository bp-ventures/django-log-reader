# Spec: ripgrep with grep fallback for log search

**Date:** 2026-04-03  
**Branch:** `feat/ripgrep-fallback`

---

## Goal

Replace the hard-coded `grep` call in `read_file_lines()` with `rg` (ripgrep) when available, falling back to `grep` when `rg` is not installed. Both paths must produce identical results for any input.

---

## Motivation

- ripgrep is significantly faster on large log files (SIMD, parallel I/O, better buffering)
- Servers that have `rg` installed should use it automatically
- Servers without it continue to work unchanged — no new hard dependency

---

## Scope

Two file changes: **`log_reader/utils.py`**, **`log_reader/tests/test_utils.py`**  
No settings, template, admin, or URL changes.

---

## Pattern semantics — the hard part

This is the most important design decision in the spec.

### Current behaviour

`log_reader/utils.py:33` passes the raw search string to `grep` with no `-E` or `-F` flag. That means **BRE (Basic Regular Expressions)**. In BRE, `+`, `?`, `(`, `)`, `{`, `|` are treated as literals unless escaped with `\`. A user typing `user+name` gets a literal match; typing `\(error\)` gets a group.

### The rg default

`rg` uses the Rust regex engine, which is **ERE-like** (extended). In ERE, `+`, `?`, `(`, `)`, `{`, `|` are metacharacters without escaping. The same string `user+name` becomes "user followed by one-or-more 'n'" — a different result.

The two engines are **not drop-in compatible**. Claiming otherwise is wrong.

### Chosen normalisation: fixed strings (`-F`) on both sides

Log searches are almost always literal: `ERROR`, `404`, `user@example.com`, `[Errno 111]`. Regex semantics in a plain search box are surprising and rarely intended.

**Both paths will use fixed-string matching:**

```
rg    →  -F / --fixed-strings
grep  →  -F / --fixed-strings
```

This is a **small, intentional behaviour change** from the current code: previously a user could accidentally (or deliberately) use BRE metacharacters. After this change, the search string is always treated as a literal substring. This is safer, faster, and what users expect.

Document this in the changelog.

### Exit codes

`grep -F` and `rg -F` have identical exit code semantics:

| Exit | Meaning |
|---|---|
| 0 | One or more matches found |
| 1 | No matches |
| 2 | Error (bad flag, unreadable file, etc.) |

The current code at `log_reader/utils.py:45` does not inspect `result.returncode` — it uses `result.stdout` directly. Exit code 1 (no matches) produces empty stdout, which `split_file_content` already handles by returning `[]`. This behaviour is preserved unchanged by this spec. No return-code handling is added.

---

## Design

### Probe at import time

Detect `rg` once at module load with `shutil.which`. Stored as a module-level constant — zero per-request overhead.

```python
_RG = shutil.which('rg')   # absolute path str, or None
```

**Operational note:** because the probe runs at import time, changing `PATH` in a running Django process has no effect. To switch backends, restart the process. This is the correct and expected behaviour for a module-level probe — do not document "remove rg from PATH" as a live toggle.

### Search command builder

```
_RG set   →  [_RG, '--no-heading', '--no-filename', '-F', '-m', str(max_lines), search, file_path]
_RG None  →  ['grep', '-F', '-m', str(max_lines), search, file_path]
```

**All flags:**

| Flag | grep | rg | Purpose |
|---|---|---|---|
| `-F` | yes | yes | Fixed-string (literal) match |
| `-m N` | yes | yes | Stop after N matches |
| `--no-heading` | — | yes | No filename header block |
| `--no-filename` | — | yes | No per-line filename prefix |

---

## File changes

### `log_reader/utils.py`

**Add** `import shutil` alongside existing imports (line 3 area).

**Add module-level constant** after imports, before `get_log_files` (currently line 15):
```python
_RG = shutil.which('rg')
```

**Add private function** before `read_file_lines` (currently line 24):
```python
def _search_cmd(search: str, file_path: str, max_lines: int) -> list[str]:
    if _RG:
        return [_RG, '--no-heading', '--no-filename', '-F', '-m', str(max_lines), search, file_path]
    return ['grep', '-F', '-m', str(max_lines), search, file_path]
```

**Replace lines 32–37** in `read_file_lines`:

Before:
```python
result = subprocess.run(
    ['grep', '-m', str(settings.LOG_READER_MAX_READ_LINES), search, file_path],
    stdout=PIPE,
    stderr=PIPE,
    encoding="utf8",
)
```

After:
```python
result = subprocess.run(
    _search_cmd(search, file_path, settings.LOG_READER_MAX_READ_LINES),
    stdout=PIPE,
    stderr=PIPE,
    encoding="utf8",
)
```

---

### `log_reader/settings.py`

No changes.

---

### `log_reader/tests/test_utils.py`

All new tests go in `ReadFileLinesTest` unless noted.

---

**Test 1 — `_search_cmd` builds rg argv correctly:**
```python
def test_search_cmd_rg_argv(self):
    from log_reader import utils as log_utils
    with mock.patch.object(log_utils, '_RG', '/usr/bin/rg'):
        cmd = log_utils._search_cmd('ERROR', '/logs/app.log', 500)
    assert cmd == ['/usr/bin/rg', '--no-heading', '--no-filename', '-F', '-m', '500', 'ERROR', '/logs/app.log']
```

**Test 2 — `_search_cmd` builds grep argv correctly:**
```python
def test_search_cmd_grep_argv(self):
    from log_reader import utils as log_utils
    with mock.patch.object(log_utils, '_RG', None):
        cmd = log_utils._search_cmd('ERROR', '/logs/app.log', 500)
    assert cmd == ['grep', '-F', '-m', '500', 'ERROR', '/logs/app.log']
```

**Test 3 — integration path passes rg argv to subprocess.run:**
```python
def test_read_file_lines_passes_rg_argv(self):
    from log_reader import utils as log_utils
    self._write('app.log', 'ERROR one\nINFO two\n')
    fake_result = mock.Mock()
    fake_result.stdout = 'ERROR one\n'
    with mock.patch.object(log_utils, '_RG', '/usr/bin/rg'), \
         mock.patch('log_reader.utils.subprocess.run', return_value=fake_result) as mock_run, \
         mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
        read_file_lines('app.log', search='ERROR')
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == '/usr/bin/rg'
    assert '-F' in called_cmd
```

**Test 4 — integration path passes grep argv to subprocess.run when rg absent:**
```python
def test_read_file_lines_passes_grep_argv(self):
    from log_reader import utils as log_utils
    self._write('app.log', 'ERROR one\nINFO two\n')
    fake_result = mock.Mock()
    fake_result.stdout = 'ERROR one\n'
    with mock.patch.object(log_utils, '_RG', None), \
         mock.patch('log_reader.utils.subprocess.run', return_value=fake_result) as mock_run, \
         mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
        read_file_lines('app.log', search='ERROR')
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == 'grep'
    assert '-F' in called_cmd
```

**Test 5 — fixed-string: regex metacharacters treated as literals:**
```python
def test_search_fixed_string_metacharacters(self):
    # A search for 'user+name' must match the literal string, not a regex
    self._write('app.log', 'user+name logged in\nuserXname ignored\n')
    with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
        ok, lines = read_file_lines('app.log', search='user+name')
    assert ok is True
    assert len(lines) == 1
    assert 'user+name' in lines[0]
```

Note: test 5 uses the real subprocess (grep or rg, whichever is available) to confirm end-to-end fixed-string behaviour. It will fail if `-F` is missing from either path.

---

## Diagram

```
request.GET['q']  (raw string, never interpreted as regex)
      │
      ▼
read_file_lines(file_name, search)
      │
      ├─ search is None ──► tail subprocess  (unchanged)
      │
      └─ search present
             │
             ▼
        _search_cmd(search, file_path, max_lines)
             │
             ├─ _RG set (probed once at import) ──► rg -F --no-heading --no-filename -m N
             └─ _RG None                         ──► grep -F -m N
             │
             ▼
        subprocess.run(cmd, stdout=PIPE, stderr=PIPE, encoding='utf8')
             │
             ▼
        result.stdout  (empty string → [] via split_file_content)
        returncode not inspected (unchanged from current behaviour)
```

---

## Changelog entry

```
- Search now uses fixed-string matching (-F) on both grep and rg paths.
  Previously grep used BRE, meaning metacharacters like +, (, | had regex
  meaning. Searches are now always treated as literal substrings.
- ripgrep (rg) is used automatically when available; falls back to grep.
```

---

## Out of scope

- Making `-F` vs regex configurable — a separate decision if operators need regex search
- Logging which binary was selected at startup — add only if operators ask
