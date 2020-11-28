from django.conf import settings
from drizm_commons.google import force_obtain_id_token
from google.oauth2 import service_account
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class TestGCPAuth(APITestCase):
    def setUp(self) -> None:
        self.url = "users:flush_expired"
        auth = service_account.IDTokenCredentials.from_service_account_file(
            settings.GS_CREDENTIALS_FILE,
            target_audience="https://example.com/"
        )
        self.token = force_obtain_id_token(auth)

    def test010_auth_perm(self):
        url = reverse(self.url)
        res = self.client.post(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        res = self.client.post(url)
        assert res.status_code == status.HTTP_200_OK

        token = self.token[:-7]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        res = self.client.post(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        self.client.credentials()
