from functools import partial
from typing import Optional
from uuid import uuid4

from django.http import QueryDict
from parameterized.parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from TimeManagerBackend.apps.notes.boards.models import NotesBoard
from ...conftest import create_test_user, self_to_id


class TestGroups(APITestCase):
    @classmethod
    def setUpClass(cls):
        app_base = "notes:groups-%s"
        cls.list = app_base % "list"
        cls.detail = app_base % "detail"

        super().setUpClass()

    def setUp(self) -> None:
        self.user = create_test_user()

        self.board = NotesBoard.objects.create(
            owner=self.user, title="Literally idk"
        )
        self.board.members.set([self.user])
        self.board.save()

    def _test_group_create_request(
            self, url: Optional[str] = None, data: Optional[dict] = None):
        return partial(
            self.client.post,
            url or reverse(self.list, args=(self.board.pk,)),
            data or {
                "title": "Shopping",
                "color": "#ffffff"
            }
        )

    def test010_create(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to create a group
            AND I am a member or the owner of the board it belongs to
        THEN I should be able to create a group
        """
        self.client.force_authenticate(user=self.user)
        req = self._test_group_create_request()
        res = req()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test020_list(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to list all groups in a board
            AND I am a member or the owner of the board it belongs to
        THEN I should be able to list all groups of that board
        """
        url = reverse(self.list, args=(self.board.pk,))

        self.client.force_authenticate(user=self.user)
        self._test_group_create_request(url=url)()

        res = self.client.get(url)
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 1)

    def test030_retrieve(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to retrieve a group
            AND I am a member or the owner of the board it belongs to
        THEN I should be able to retrieve that group
        """
        self.client.force_authenticate(user=self.user)
        req = self._test_group_create_request()
        res = req()
        content = res.json()
        pk = self_to_id(content)

        url = reverse(
            self.detail, args=(self.board.pk, pk)
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test040_update(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to update a group
            AND I am a member or the owner of the board it belongs to
        THEN I should be able to update that group
        """
        self.client.force_authenticate(user=self.user)
        req = self._test_group_create_request()
        res = req()
        content = res.json()
        pk = self_to_id(content)

        url = reverse(
            self.detail, args=(self.board.pk, pk)
        )
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @parameterized.expand([(False,), (True,)])
    def test050_delete(self, cascade):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to delete a group
            AND I am a member or the owner of the board it belongs to
        THEN I should be able to delete that group
        """
        self.client.force_authenticate(user=self.user)
        req = self._test_group_create_request()
        res = req()
        content = res.json()
        pk = self_to_id(content)

        # Add a note to the group
        note_pk = uuid4()
        url = reverse(
            "notes:groups-notes", args=(self.board.pk, pk, note_pk)
        )
        res = self.client.put(url, data={"content": "Lol idk"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        boards_url = reverse(
            "notes:boards-detail", args=(self.board.pk,)
        )
        res = self.client.get(boards_url)
        notes_count = len(res.json().get("notes"))

        url = reverse(
            self.detail, args=(self.board.pk, pk)
        )
        q = QueryDict(mutable=True)
        q["cascade"] = cascade
        url = f"{url}?{q.urlencode()}"
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        res = self.client.get(boards_url)
        notes = res.json().get("notes")
        if cascade:
            self.assertEqual(len(notes), notes_count)
        else:
            self.assertGreater(len(notes), notes_count)
