from functools import partial
from typing import Optional

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from TimeManagerBackend.apps.notes.boards.models import NotesBoard
from ...conftest import create_test_user, self_to_id


class TestNotesBoards(APITestCase):
    @classmethod
    def setUpClass(cls):
        app_list = "notes:boards-%s"
        cls.list = app_list % "list"
        cls.detail = app_list % "detail"

        super().setUpClass()

    def setUp(self) -> None:
        self.user = create_test_user()

        self.member_pw = "literallyAnything55"
        self.member = create_test_user(
            "someguy@reddit.com", self.member_pw
        )

    def _get_create_board_partial(
            self, url: str, data: Optional[dict] = None
    ):
        return partial(
            self.client.post,
            url,
            data or {"title": "Some Board", "members": [self.member.pk]}
        )

    def test010_create(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to create a new board
        THEN I should be able to create a new board
        """
        url = reverse(self.list)

        request = self._get_create_board_partial(url)
        res = request()
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        res = request()
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            self_to_id(content.get("owner")),
            self.user.pk
        )
        assert any(
            [self.user.pk == self_to_id(m) for m in content.get("members")]
        )

    def test020_retrieve(self):
        """
        GIVEN I have a user account
            AND I am loggged in
        WHEN I ask to retrieve an existing board
            AND I am a member or the owner of that board
        THEN I should be able to retrieve that board
        """
        request = self._get_create_board_partial(reverse(self.list))
        self.client.force_authenticate(user=self.user)
        content = request().json()
        board_id = self_to_id(content)

        url = reverse(self.detail, args=(board_id,))

        # The owner should be able to retrieve the board
        res = self.client.get(url)
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        members = content.get("members")
        self.assertEqual(type(members), list)
        self.assertGreaterEqual(len(members), 1)
        # Make sure that members contains the full instances
        # not just primary keys
        self.assertEqual(type(members[0]), dict)

        # A member should also be able to retrieve the board
        self.client.force_authenticate(user=self.member)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # A user that is neither a member or the owner SHOULD NOT
        # be able to retrieve the board
        test_user = create_test_user("iuhguzr@ok.com", "imSickOfTesting123")
        self.client.force_authenticate(test_user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test030_list(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to list all boards
        THEN I should get a list of all boards,
        that I own or am a member of
        """
        url = reverse(self.list)

        request = self._get_create_board_partial(
            url, {"title": "AnotherBoard"}
        )
        self.client.force_authenticate(user=self.user)
        request()

        # As we are the owner we should be able to see the board
        res = self.client.get(url)
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 1)

        # Another user should not be able to see any boards
        self.client.force_authenticate(user=self.member)
        res = self.client.get(url)
        content = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 0)

    def test040_update(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to update a board
            AND I am the owner of that board
        THEN I should be able to update that board
        """
        request = self._get_create_board_partial(reverse(self.list))
        self.client.force_authenticate(user=self.user)
        content = request().json()
        board_id = self_to_id(content)

        url = reverse(self.detail, args=(board_id,))

        res = self.client.patch(url, {"title": "Changed Board"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.member)
        res = self.client.patch(url, {"title": "Changed Board"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test050_delete(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to delete a board
            AND I am the owner of that board
        THEN I should be able to delete that board
        """
        request = self._get_create_board_partial(reverse(self.list))
        self.client.force_authenticate(user=self.user)
        content = request().json()
        board_id = self_to_id(content)

        url = reverse(self.detail, args=(board_id,))

        self.client.force_authenticate(user=self.member)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


class TestBoardMembers(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user()
        cls.member = create_test_user("123456a@okay.com", "ihhzotnhoirt")

        cls.list = "notes:boards-members"

        # Create a board for testing
        cls.board = NotesBoard.objects.create(
            owner=cls.user, title="Some Testing Board"
        )
        cls.board.members.set([cls.user])
        cls.board.save()

        cls.url = reverse(cls.list, args=(cls.board.pk,))

    def test010_add(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to add a member to a board
            AND I am the owner of that board
        THEN I should be able to add a member to that board
        """
        self.client.force_authenticate(user=self.user)
        # Operation is idempotent so nothing should change
        # if we perform it multiple times
        for _ in range(2):
            res = self.client.put(self.url, {"members": [self.member.pk]})
            members = res.json().get("members")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(type(members), list)
            self.assertEqual(len(members), 2)

    def test020_remove(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to remove a member from a board
            AND I am the owner of that board
        THEN I should be able to remove a member from that board
        """
        self.client.force_authenticate(user=self.user)
        # Operation is idempotent so nothing should change
        # if we perform it multiple times
        for _ in range(2):
            res = self.client.delete(self.url, {"members": [self.member.pk]})
            members = res.json().get("members")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(type(members), list)
            self.assertEqual(len(members), 1)

        # Make sure we cannot remove the owner
        res = self.client.delete(self.url, {"members": [self.user.pk]})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
