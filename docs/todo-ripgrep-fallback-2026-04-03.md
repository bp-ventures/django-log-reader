# Todo: ripgrep with grep fallback

**Spec:** `docs/log-reader-ripgrep-fallback-2026-04-03.md`  
**Branch:** `feat/ripgrep-fallback`

---

## Checklist

### 1. `log_reader/utils.py`

- [ ] Add `import shutil` alongside existing imports (after line 3)
- [ ] Add module-level constant after imports, before `get_log_files` (line 15):
  ```python
  _RG = shutil.which('rg')
  ```
- [ ] Add `_search_cmd` before `read_file_lines` (line 24):
  ```python
  def _search_cmd(search: str, file_path: str, max_lines: int) -> list[str]:
      if _RG:
          return [_RG, '--no-heading', '--no-filename', '-F', '-m', str(max_lines), search, file_path]
      return ['grep', '-F', '-m', str(max_lines), search, file_path]
  ```
- [ ] Replace lines 32–37 (grep subprocess call):
  ```python
  result = subprocess.run(
      _search_cmd(search, file_path, settings.LOG_READER_MAX_READ_LINES),
      stdout=PIPE,
      stderr=PIPE,
      encoding="utf8",
  )
  ```

### 2. `log_reader/tests/test_utils.py`

- [ ] Test 1 — `_search_cmd` builds exact rg argv:
  ```python
  def test_search_cmd_rg_argv(self):
      from log_reader import utils as log_utils
      with mock.patch.object(log_utils, '_RG', '/usr/bin/rg'):
          cmd = log_utils._search_cmd('ERROR', '/logs/app.log', 500)
      assert cmd == ['/usr/bin/rg', '--no-heading', '--no-filename', '-F', '-m', '500', 'ERROR', '/logs/app.log']
  ```
- [ ] Test 2 — `_search_cmd` builds exact grep argv:
  ```python
  def test_search_cmd_grep_argv(self):
      from log_reader import utils as log_utils
      with mock.patch.object(log_utils, '_RG', None):
          cmd = log_utils._search_cmd('ERROR', '/logs/app.log', 500)
      assert cmd == ['grep', '-F', '-m', '500', 'ERROR', '/logs/app.log']
  ```
- [ ] Test 3 — integration path passes rg argv to subprocess.run:
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
- [ ] Test 4 — integration path passes grep argv when rg absent:
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
- [ ] Test 5 — metacharacters treated as literals end-to-end (real subprocess):
  ```python
  def test_search_fixed_string_metacharacters(self):
      self._write('app.log', 'user+name logged in\nuserXname ignored\n')
      with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
          ok, lines = read_file_lines('app.log', search='user+name')
      assert ok is True
      assert len(lines) == 1
      assert 'user+name' in lines[0]
  ```

### 3. Run tests

- [ ] `uv run python -m django test log_reader.tests` passes with `DJANGO_SETTINGS_MODULE=log_reader.tests.settings`

### 4. Changelog / README

- [ ] Note in changelog: search now uses `-F` fixed-string matching on both paths; previously grep used BRE
