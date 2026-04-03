import tempfile
from unittest import mock

from django.test import TestCase

from log_reader import settings as log_settings
from log_reader.utils import read_file_lines


class PathTraversalTest(TestCase):

    def test_dotdot_rejected(self):
        with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', tempfile.mkdtemp()):
            ok, msg = read_file_lines('../../etc/passwd')
        assert ok is False

    def test_absolute_path_rejected(self):
        with mock.patch.object(log_settings, 'LOG_READER_DIR_PATH', tempfile.mkdtemp()):
            ok, msg = read_file_lines('/etc/passwd')
        assert ok is False
