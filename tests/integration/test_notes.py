from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
import uuid
from TimeManagerBackend.apps.notes.models import Note
from drizm_commons import utils


class TestNotes(APITestCase):
    def setUp(self) -> None:
        self.base = "notes:note-%s"
        self.list = self.base % "list"
        self.detail = self.base % "detail"

        self.user = get_user_model().objects.create_user(
            email="tester@tester.de",
            password="topTierthingy42"
        )

    def test010_create(self):
        pk = uuid.uuid4()
        url = reverse(self.detail, args=(pk,))
        res = self.client.post(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        self.client.force_authenticate(user=self.user)
        res = self.client.put(url, data={
            "content": "Something else idk"
        })
        assert res.status_code == status.HTTP_200_OK
        assert Note.objects.get(pk=pk).creator == self.user

        res = self.client.put(url, data={
            "content": "Again Something else idk"
        })
        assert res.status_code == status.HTTP_200_OK
        self.client.force_authenticate(user=None)

    def test020_retrieve(self):
        pk = uuid.uuid4()
        url = reverse(self.detail, args=(pk,))
        self.client.force_authenticate(user=self.user)
        self.client.put(url, data={
            "content": "Something else idk"
        })

        url = reverse(self.list)
        res = self.client.get(url)
        content = res.json()
        assert res.status_code == status.HTTP_200_OK
        assert type(content) == list
        assert len(content) == 1
        entity = content[0]
        assert utils.all_keys_present(entity, ("self", "content"))
        self.client.force_authenticate(user=None)
