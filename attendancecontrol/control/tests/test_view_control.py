from django.test import TestCase
from django.urls import reverse


class TestRedirectRoot(TestCase):
    def test_redirect_root_redirects_to_home(self):
        response = self.client.get('')
        self.assertRedirects(response, reverse('home'))
