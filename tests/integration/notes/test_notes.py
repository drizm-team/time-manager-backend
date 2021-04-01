import uuid
from operator import attrgetter

from parameterized.parameterized import parameterized_class
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from TimeManagerBackend.apps.notes.boards.models import NotesBoard
from TimeManagerBackend.apps.notes.groups.models import NotesGroup
from ...conftest import create_test_user


@parameterized_class(
    ("base_url", "url_args", "group"),
    [
        ("notes:boards-notes", (attrgetter("board.pk"),), None),
        (
                "notes:groups-notes",
                (attrgetter("board.pk"), attrgetter("group.pk")),
                {"title": "Some Group", "color": int("ffffff", 16)}
        )
    ]
)
class TestNotes(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.member = create_test_user(
            "randomMail@okay.com", "iudbgiubrgiubeiru420"
        )

        self.board = NotesBoard.objects.create(
            owner=self.user, title="Okay Son"
        )
        self.board.members.set([self.user])
        self.board.save()

        if self.group:
            self.group = NotesGroup.objects.create(
                parent=self.board, **self.group
            )

    def _get_url(self) -> str:
        return reverse(
            self.base_url,
            [arg(self) for arg in self.url_args] + [str(uuid.uuid4())]
        )

    def test010_upsert(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to upsert a note
            AND I am a member or the owner of the board that it belongs to
            AND I generated a UUIDv4 as a primary identifier for the Note
        THEN I should be able to create a note if it did not exist previously
            OR update one that did exist previously
        """
        url = self._get_url()

        self.client.force_authenticate(user=self.user)
        res = self.client.put(url, {
            "content": "literally no idea"
        })
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Make sure updating works as expected
        res = self.client.put(url, {
            "content": "Changed the content"
        })
        new_content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotEqual(
            new_content.get("last_edited"),
            content.get("last_edited")
        )

        if not self.group:
            url = reverse("notes:boards-detail", args=(self.board.pk,))
        else:
            url = reverse(
                "notes:groups-detail", args=(self.board.pk, self.group.pk)
            )

        res = self.client.get(url)
        content = res.json()
        notes = content.get("notes")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(type(notes), list)
        self.assertGreater(len(notes), 0)

    def test020_delete(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to delete a note
            AND I am a member or the owner of the board that it belongs to
        THEN I should be able to delete that note
        """
        url = self._get_url()

        self.client.force_authenticate(user=self.user)
        self.client.put(url, {
            "content": "midrtniutnhoiudrntzoindrotunodrnzi setnieu5rz"
        })

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
