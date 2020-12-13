from base64 import b64encode

from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ...conftest import create_test_user, obtain_tokens, TEST_USER_PASSWORD


class TestPrometheus(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.user_pw = TEST_USER_PASSWORD

        self.url = "prometheus_django_metrics"

    def test010_prometheus_default_auth(self):
        """
        GIVEN I have an active user account
            AND I am authenticating using JWTAuth
        WHEN I request to get the Prometheus service metrics
        THEN I should not be able to get the Prometheus service metrics
        """
        url = reverse(self.url)

        # Try and fetch without auth, this should fail
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Obtain a test token and try using it on a different endpoint
        # This should work
        access_token, *_ = obtain_tokens(self, {
            "email": self.user.email,
            "password": self.user_pw
        })
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        res = self.client.get(
            reverse("users:user-list")
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Try the same setup with default JWTAuth on the prom endpoint
        # This should fail as only the Prometheus user,
        # should be able to use the endpoint through BasicAuth
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test020_prometheus_correct_auth(self):
        """
        GIVEN I am the Prometheus user
            AND I am authenticating using BasicAuth
        WHEN I request to get the Prometheus service metrics
        THEN I should be able to get the Prometheus service metrics
        """
        url = reverse(self.url)

        # Try with correct authentication but as the test user
        # This should fail
        credentials = b64encode(
            f"{self.user.email}:{self.user_pw}".encode("utf-8"))
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Basic {credentials.decode('utf-8')}"
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Try with correct authentication as the prometheus user
        # This should work
        credentials = b64encode(
            f"{settings.PROM_USER}:{settings.PROM_PASSWORD}".encode("utf-8"))
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Basic {credentials.decode('utf-8')}"
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
