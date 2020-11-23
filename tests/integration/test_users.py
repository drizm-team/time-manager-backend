from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from drizm_commons import utils
from django.contrib.auth import get_user_model


class TestUsers(APITestCase):
    def setUp(self) -> None:
        self.app_base = "users:user-%s"
        self.list = self.app_base % "list"
        self.detail = self.app_base % "detail"

        User = get_user_model()
        User.objects.create_user(
            email="realuser@tester.de",
            password="ShittySecurity69"
        )
        self.user = User.objects.get(id=1)

    def test010_create(self):
        url = reverse(self.list)
        res = self.client.post(url, data={
            "email": "tester@tester.de",
            "password": "somePassword420"
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert list(res.json().keys()) == ["self", "email"]

        res = self.client.post(url, data={
            "email": "tester@tester.de",
            "password": "somePassword420"
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        res = self.client.post(url, data={
            "email": "f",
            "password": "somePassword420"
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test020_list(self):
        url = reverse(self.list)
        res = self.client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        content = res.json()
        assert res.status_code == status.HTTP_200_OK
        assert type(content) == list and len(content) == 1
        assert [
            utils.all_keys_present(u, ("self", "email")) for u in content
        ]
        self.client.force_authenticate(user=None)

    def test030_retrieve(self):
        url = reverse(self.detail, args=(1,))
        res = self.client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        content = res.json()
        assert res.status_code == status.HTTP_200_OK
        assert type(content) == dict
        assert utils.all_keys_present(content, ("self", "email"))
        assert utils.url_is_http(content["self"]["href"])

        url = reverse(self.detail, args=(3,))
        res = self.client.get(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND

        self.client.force_authenticate(user=None)

    def test040_update(self):
        url = reverse(self.detail, args=(1,))
        res = self.client.patch(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        self.client.force_authenticate(user=self.user)
        update_data = {
            "email": "okay@tester.de"
        }
        get_user_model().objects.create_user(
            email="sth@tester.de",
            password="ubtiubbiuioubiuni"
        )

        res = self.client.put(url, update_data)
        assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        for _ in range(2):
            res = self.client.patch(url, update_data)
            assert res.status_code == status.HTTP_200_OK

        res = self.client.patch(url, {"email": "sth@tester.de"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        url = reverse(self.detail, args=(5,))
        res = self.client.patch(url, {"email": "sth@tester.de"})
        assert res.status_code == status.HTTP_404_NOT_FOUND

        self.client.force_authenticate(user=None)

    def test050_delete(self):
        url = reverse(self.detail, args=(1,))
        res = self.client.delete(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        get_user_model().objects.create_user(
            email="sth@tester.de",
            password="ubtiubbiuioubiuni"
        )

        self.client.force_authenticate(user=self.user)
        url = reverse(self.detail, args=(2,))
        res = self.client.delete(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND

        url = reverse(self.detail, args=(1,))
        res = self.client.delete(url)
        assert res.status_code == status.HTTP_204_NO_CONTENT

        self.client.force_authenticate(user=None)
