from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..conftest import obtain_tokens, create_test_user, TEST_USER_PASSWORD


class TestTokens(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.user_pw = TEST_USER_PASSWORD

        self.obtain = "tokens:obtain_delete"
        self.verify = "tokens:verify"
        self.refresh = "tokens:refresh"

    def test010_obtain(self):
        """
        GIVEN I have a user account
            AND valid credentials for that account
        WHEN I ask to create a token pair
        THEN I should receive a valid access / refresh token pair
        """
        *_, res = obtain_tokens(self, {
            "email": self.user.email,
            "password": self.user_pw
        })
        content = res.json()
        assert res.status_code == status.HTTP_200_OK
        self.assertListEqual(
            list(content.keys()),
            ["refresh", "access"]
        )

    def test020_verify(self):
        """
        GIVEN I have a valid refresh or access token
        WHEN I ask if the token is valid
        THEN I should receive confirmation that it is
            AND The behaviour is identical for both types of tokens
        """
        url = reverse(self.verify)

        access_token, refresh_token, _ = obtain_tokens(self, {
            "email": self.user.email,
            "password": self.user_pw
        })

        # Valid access token should come back as being valid
        # But without indication of its type
        res_access = self.client.post(url, data={"token": access_token})
        self.assertEqual(res_access.status_code, status.HTTP_200_OK)

        # Same for a valid refresh token
        res_refresh = self.client.post(url, data={"token": refresh_token})
        self.assertEqual(res_refresh.status_code, status.HTTP_200_OK)

        # Make sure both responses really were identical
        # as to not give away the type of token
        self.assertEqual(res_access.status_code, res_refresh.status_code)
        self.assertEqual(res_access.json(), res_refresh.json())

        # A random nonsensical token should not pass
        res = self.client.post(url, data={"token": "ubuzbr"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test030_delete(self):
        """
        GIVEN I have a token pair
        WHEN I ask to delete the refresh token
        THEN the refresh token should no longer work
            AND the access token should still work
        """
        url = reverse(self.obtain)

        access_token, refresh_token, _ = obtain_tokens(self, {
            "email": self.user.email,
            "password": self.user_pw
        })

        # Delete the refresh token
        # this should work as it is a valid token
        res = self.client.delete(url, data={"refresh": refresh_token})
        self.assertEqual(res.status_code, status.HTTP_205_RESET_CONTENT)

        # Attempt to delete the access token
        # this should not work because blacklisting is only applicable
        # for refresh tokens
        res = self.client.delete(url, data={"refresh": access_token})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Attempt to delete a nonsensical token
        # This should fail with a 401
        res = self.client.delete(url, data={"refresh": "iungjhbghibikju"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test040_refresh(self):
        """
        GIVEN I have a valid refresh token
        WHEN I ask to generate a new access token from that refresh token
        THEN I should receive a valid access token
        """
        url = reverse(self.refresh)

        _, refresh_token, _ = obtain_tokens(self, {
            "email": self.user.email,
            "password": self.user_pw
        })

        # Attempt to retrieve an access token from a refresh token
        # This should work and return a valid token
        # because the refresh token is valid
        res = self.client.post(url, data={"refresh": refresh_token})
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            list(content.keys()),
            ["access"]
        )

        # Attempt to retrieve a token through an invalid refresh token
        # this should fail with a 401
        res = self.client.post(url, data={"refresh": "drhdrtzdrt"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
