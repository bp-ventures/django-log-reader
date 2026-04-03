import django

if django.VERSION >= (4, 0):
    from django.utils.translation import gettext_lazy as _
else:
    from django.utils.translation import ugettext_lazy as _


class FileLogReader(object):
    class Meta(object):
        app_label = 'log_reader'
        object_name = 'file_log_readers'
        model_name = module_name = 'file_log_readers'
        verbose_name = _('file log')
        verbose_name_plural = _('file logs')
        abstract = False
        swapped = False
        is_composite_pk = False
        app_config = ""

    _meta = Meta()
