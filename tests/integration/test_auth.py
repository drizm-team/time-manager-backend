from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status


class TestAuth(APITestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user_pw = "ShittySecurity69"
        User.objects.create_user(
            email="realuser@tester.de",
            password=self.user_pw
        )
        self.user = User.objects.get(id=1)

        self.obtain = reverse("token_obtain_pair")
        self.verify = reverse("token_verify")
        self.refresh = reverse("token_refresh")

    def self_obtain_tokens(self, credentials: dict):
        return self.client.post(self.obtain, data=credentials)

    def test010_tokens(self):
        res = self.self_obtain_tokens({
            "email": self.user.email,
            "password": self.user_pw
        })
        content = res.json()
        assert res.status_code == status.HTTP_200_OK
        assert list(content.keys()) == ["refresh", "access"]

    def test020_authenticate(self):
        res = self.self_obtain_tokens({
            "email": self.user.email,
            "password": self.user_pw
        })
        access_token = res.json().get("access")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        res = self.client.get(
            reverse("users:user-list")
        )
        assert res.status_code == status.HTTP_200_OK

    def test030_verify(self):
        res = self.self_obtain_tokens({
            "email": self.user.email,
            "password": self.user_pw
        })
        access_token = res.json().get("access")
        res = self.client.post(self.verify, data={"token": access_token})
        assert res.status_code == status.HTTP_200_OK

        res = self.client.post(self.verify, data={"token": "ubuzbr"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test040_refresh(self):
        res = self.self_obtain_tokens({
            "email": self.user.email,
            "password": self.user_pw
        })
        refresh_token = res.json().get("refresh")
        res = self.client.post(self.refresh, data={"refresh": refresh_token})
        assert res.status_code == status.HTTP_200_OK

        res = self.client.post(self.refresh, data={"refresh": "drhdrtzdrt"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
