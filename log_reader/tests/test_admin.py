from django.contrib import admin
from django.test import TestCase

from log_reader.admin import FileLogReaderAdmin
from log_reader.models import FileLogReader


class AdminRegistrationTest(TestCase):

    def test_model_is_registered(self):
        assert admin.site.is_registered(FileLogReader)

    def test_admin_class(self):
        model_admin = admin.site.get_model_admin(FileLogReader)
        assert isinstance(model_admin, FileLogReaderAdmin)

    def test_get_urls_returns_patterns(self):
        model_admin = admin.site.get_model_admin(FileLogReader)
        urls = model_admin.get_urls()
        assert len(urls) == 1
        assert 'log_reader_file_log_readers_changelist' in urls[0].name
