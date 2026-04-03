import os
import tempfile
from unittest import mock

from django.test import TestCase

from log_reader import settings as log_settings
from log_reader.utils import get_log_files, read_file_lines, split_file_content


class GetLogFilesTest(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _touch(self, name):
        path = os.path.join(self.tmpdir, name)
        open(path, "w").close()
        return path

    def test_returns_matching_files(self):
        self._touch("app.log")
        self._touch("other.txt")
        result = get_log_files(self.tmpdir)
        assert result == ["app.log"]

    def test_excludes_files(self):
        self._touch("app.log")
        self._touch("debug.log")
        with mock.patch.object(log_settings, "LOG_READER_EXCLUDE_FILES", ["debug.log"]):
            result = get_log_files(self.tmpdir)
        assert result == ["app.log"]

    def test_empty_for_nonexistent_dir(self):
        result = get_log_files("/tmp/nonexistent_dir_12345")
        assert result == []

    def test_ignores_tilde_files(self):
        self._touch("app.log~")
        self._touch("app.log")
        result = get_log_files(self.tmpdir)
        assert result == ["app.log"]


class ReadFileLinesTest(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_missing_file_returns_false(self):
        with mock.patch.object(log_settings, "LOG_READER_DIR_PATH", self.tmpdir):
            ok, msg = read_file_lines("nonexistent.log")
        assert ok is False

    def test_reads_valid_file(self):
        self._write("app.log", "line one\nline two\nline three\n")
        with mock.patch.object(log_settings, "LOG_READER_DIR_PATH", self.tmpdir):
            ok, lines = read_file_lines("app.log")
        assert ok is True
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_search_filters_lines(self):
        self._write("app.log", "ERROR something broke\nINFO all good\nERROR again\n")
        with mock.patch.object(log_settings, "LOG_READER_DIR_PATH", self.tmpdir):
            ok, lines = read_file_lines("app.log", search="ERROR")
        assert ok is True
        for line in lines:
            assert "ERROR" in line

    def test_search_cmd_rg_argv(self):
        from log_reader import utils as log_utils

        with mock.patch.object(log_utils, "_RG", "/usr/bin/rg"):
            cmd = log_utils._search_cmd("ERROR", "/logs/app.log", 500)
        assert cmd == ["/usr/bin/rg", "--no-heading", "--no-filename", "-F", "-m", "500", "ERROR", "/logs/app.log"]

    def test_search_cmd_grep_argv(self):
        from log_reader import utils as log_utils

        with mock.patch.object(log_utils, "_RG", None):
            cmd = log_utils._search_cmd("ERROR", "/logs/app.log", 500)
        assert cmd == ["grep", "-F", "-m", "500", "ERROR", "/logs/app.log"]

    def test_read_file_lines_passes_rg_argv(self):
        from log_reader import utils as log_utils

        self._write("app.log", "ERROR one\nINFO two\n")
        fake_result = mock.Mock()
        fake_result.stdout = "ERROR one\n"
        with mock.patch.object(log_utils, "_RG", "/usr/bin/rg"), mock.patch("log_reader.utils.subprocess.run", return_value=fake_result) as mock_run, mock.patch.object(
            log_settings, "LOG_READER_DIR_PATH", self.tmpdir
        ):
            read_file_lines("app.log", search="ERROR")
        called_cmd = mock_run.call_args[0][0]
        assert called_cmd[0] == "/usr/bin/rg"
        assert "-F" in called_cmd

    def test_read_file_lines_passes_grep_argv(self):
        from log_reader import utils as log_utils

        self._write("app.log", "ERROR one\nINFO two\n")
        fake_result = mock.Mock()
        fake_result.stdout = "ERROR one\n"
        with mock.patch.object(log_utils, "_RG", None), mock.patch("log_reader.utils.subprocess.run", return_value=fake_result) as mock_run, mock.patch.object(
            log_settings, "LOG_READER_DIR_PATH", self.tmpdir
        ):
            read_file_lines("app.log", search="ERROR")
        called_cmd = mock_run.call_args[0][0]
        assert called_cmd[0] == "grep"
        assert "-F" in called_cmd

    def test_search_fixed_string_metacharacters(self):
        self._write("app.log", "user+name logged in\nuserXname ignored\n")
        with mock.patch.object(log_settings, "LOG_READER_DIR_PATH", self.tmpdir):
            ok, lines = read_file_lines("app.log", search="user+name")
        assert ok is True
        assert len(lines) == 1
        assert "user+name" in lines[0]


class SplitFileContentTest(TestCase):
    def test_splits_on_newline(self):
        result = split_file_content("hello world\\nfoo bar baz")
        assert len(result) == 2

    def test_filters_short_lines(self):
        result = split_file_content("hello world\\nab\\nfoo bar baz")
        assert all(len(x) > 5 for x in result)

    def test_none_returns_empty(self):
        assert split_file_content(None) == []
