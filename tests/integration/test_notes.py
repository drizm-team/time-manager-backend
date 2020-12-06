import uuid

from drizm_commons import utils
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from TimeManagerBackend.apps.notes.models import Note
from ..conftest import create_test_user, TEST_USER_PASSWORD


class TestNotes(APITestCase):
    def setUp(self) -> None:
        app_base = "notes:note-%s"
        self.list = app_base % "list"
        self.detail = app_base % "detail"

        self.user_pw = TEST_USER_PASSWORD
        self.user = create_test_user()

    def test010_create(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to create a new Note
            AND I generate a UUID as a primary identifier for the Note
        THEN I should be able to create a new note
        """
        pk = uuid.uuid4()
        url = reverse(self.detail, args=(pk,))

        # Should not work here because we are not logged in
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Create a new note, while being logged in
        # This should work
        self.client.force_authenticate(user=self.user)
        res = self.client.put(url, data={
            "content": "Something else idk"
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user, Note.objects.get(pk=pk).creator)
        assert utils.all_keys_present(res.json(), ("self", "content"))

        # Create a note without specifying any body,
        # thus not providing any content
        # This should work
        pk = uuid.uuid4()
        url = reverse(self.detail, args=(pk,))
        res = self.client.put(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Create a new note while specifying empty content
        # This should work
        pk = uuid.uuid4()
        url = reverse(self.detail, args=(pk,))
        res = self.client.put(url, data={"content": ""})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test020_overwrite(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to overwrite an existing note
            AND that note was created by mself
        THEN I should be able to overwrite an existing note
        """
        pk = uuid.uuid4()
        url = reverse(self.detail, args=(pk,))

        # Create a note as the test user
        # This should work fine
        self.client.force_authenticate(user=self.user)
        res = self.client.put(url, data={
            "content": "some Content :)"
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Overwrite the note from before
        # This should work
        res = self.client.put(url, data={
            "content": "changed some stuff"
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Create a new test user and attempt to have the note
        # overwritten by them, this should not work
        test_user = create_test_user(
            email="someMailmm@domain.com",
            password="iuoiheriudeirutisertnh"
        )
        self.client.force_authenticate(user=test_user)
        res = self.client.put(url, data={
            "content": "I wanna overwrite this!"
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
