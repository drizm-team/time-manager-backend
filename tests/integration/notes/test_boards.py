from rest_framework.test import APITestCase
from ...conftest import create_test_user, TEST_USER_PASSWORD, self_to_id
from rest_framework.reverse import reverse
from functools import partial
from rest_framework import status


class TestNotesBoards(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user()
        cls.user_pw = TEST_USER_PASSWORD

        cls.member_pw = "literallyAnything55"
        cls.member = create_test_user(
            "someguy@reddit.com", cls.member_pw
        )

        app_list = "notes:boards-%s"
        cls.list = app_list % "list"
        cls.detail = app_list % "detail"

    def test010_boards_create(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to create a new board
        THEN I should be able to create a new board
        """
        url = reverse(self.list)

        request = partial(
            self.client.post,
            url,
            {"title": "Some Board", "members": [self.member.pk]}
        )
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
        self.assertIn(self.user.pk, content.get("members"))
