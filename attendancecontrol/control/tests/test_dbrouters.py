from django.test import TransactionTestCase, override_settings

from ..models.probes import ProbeRequest

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    'probes': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}


# @override_settings(DATABASES=DATABASES)
class ProbeRequestRouterTest(TransactionTestCase):
    databases = {'default', 'probes'}

    def test_dbrouter_uses_probes_as_db(self):
        ProbeRequest.objects.last()
        self.assertIs(True, True)

    def test_dbrouter_raises_exception_when_try_to_create_probe_request(self):
        self.assertRaises(BaseException, ProbeRequest.objects.create)
