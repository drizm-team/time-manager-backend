from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from drizm_commons.testing.truthiness import all_keys_present


class TestCors(APITestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["https://example.org"])
    def test010_cors_preflight(self):
        viewname = "tokens:obtain_delete"
        url = reverse(viewname)
        res = self.client.options(
            url,
            HTTP_ORIGIN="http://example.org",
            Access_Control_Request_Method="POST"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        assert all_keys_present(
            res._headers,
            ('access-control-allow-origin',),
            strict=False
        )
