from django.test import TestCase

from log_reader.models import FileLogReader


class FileLogReaderMetaTest(TestCase):
    def test_required_admin_attrs_exist(self):
        """Meta has all attributes Django admin.register() checks."""
        meta = FileLogReader._meta
        assert meta.app_label == "log_reader"
        assert meta.abstract is False
        assert meta.swapped is False

    def test_is_composite_pk(self):
        """Django 6.0 checks this on admin registration."""
        assert FileLogReader._meta.is_composite_pk is False

    def test_model_name(self):
        assert FileLogReader._meta.model_name == "file_log_readers"

    def test_verbose_names(self):
        assert str(FileLogReader._meta.verbose_name) == "file log"
        assert str(FileLogReader._meta.verbose_name_plural) == "file logs"
