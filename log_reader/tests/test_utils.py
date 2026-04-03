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
        open(path, 'w').close()
        return path

    def test_returns_matching_files(self):
        self._touch('app.log')
        self._touch('other.txt')
        result = get_log_files(self.tmpdir)
        assert result == ['app.log']

    def test_excludes_files(self):
        self._touch('app.log')
        self._touch('debug.log')
        with mock.patch.object(log_settings, 'LOG_READER_EXCLUDE_FILES', ['debug.log']):
            result = get_log_files(self.tmpdir)
        assert result == ['app.log']

    def test_empty_for_nonexistent_dir(self):
        result = get_log_files('/tmp/nonexistent_dir_12345')
        assert result == []

    def test_ignores_tilde_files(self):
        self._touch('app.log~')
        self._touch('app.log')
        result = get_log_files(self.tmpdir)
        assert result == ['app.log']


class ReadFileLinesTest(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_missing_file_returns_false(self):
        with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
            ok, msg = read_file_lines('nonexistent.log')
        assert ok is False

    def test_reads_valid_file(self):
        self._write('app.log', 'line one\nline two\nline three\n')
        with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
            ok, lines = read_file_lines('app.log')
        assert ok is True
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_search_filters_lines(self):
        self._write('app.log', 'ERROR something broke\nINFO all good\nERROR again\n')
        with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', self.tmpdir):
            ok, lines = read_file_lines('app.log', search='ERROR')
        assert ok is True
        for line in lines:
            assert 'ERROR' in line


class SplitFileContentTest(TestCase):

    def test_splits_on_newline(self):
        result = split_file_content('hello world\\nfoo bar baz')
        assert len(result) == 2

    def test_filters_short_lines(self):
        result = split_file_content('hello world\\nab\\nfoo bar baz')
        assert all(len(x) > 5 for x in result)

    def test_none_returns_empty(self):
        assert split_file_content(None) == []
