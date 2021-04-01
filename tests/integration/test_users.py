import random
import string

from django.contrib.auth import get_user_model
from django.core.files.storage import get_storage_class
from drizm_commons.testing.truthiness import all_keys_present, uri_is_http
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from storages.backends.gcloud import GoogleCloudStorage

from ..conftest import (
    create_test_user,
    TEST_USER_PASSWORD,
    self_to_id,
    generate_test_image,
    generate_image_b64,
    random_hex_color
)
from ..data.b64 import IMG


class TestUsers(APITestCase):
    @classmethod
    def setUpClass(cls):
        app_base = "users:user-%s"
        cls.list = app_base % "list"
        cls.detail = app_base % "detail"
        cls.change_password = app_base % "change-password"
        cls.change_email = app_base % "change-email"

        cls._storage: GoogleCloudStorage = get_storage_class()
        cls.storage = cls._storage.client

        super().setUpClass()

    def setUp(self) -> None:
        self.user = create_test_user()
        self.user_pw = TEST_USER_PASSWORD

    # noinspection PyMethodMayBeStatic
    def _test_response_body(self, body: dict):
        # Response Body should contain 'self', 'email', 'profile_picture'
        # and the names 'first_name' and 'last_name', both which should be present,
        # even if their value is NULL
        assert all_keys_present(
            body, (
                "self", "email", "first_name", "last_name", "profile_picture"
            )
        )
        assert all_keys_present(
            body.get("profile_picture"), ("image", "background")
        )

    # noinspection PyMethodMayBeStatic
    def _test_user_data(self) -> dict:
        email = f"{''.join(random.choices(string.ascii_letters, k=8))}@tester.de"
        return {
            "email": email,
            "password": "somePasswordIdc",
            "profile_picture": {
                "background": random_hex_color()
            }
        }

    def test010_retrieve(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to retrieve a user
            AND that user is myself
        THEN I should be able to see the details of that user
        """
        url = reverse(self.detail, args=(self.user.pk,))

        # Should only work when we are logged in
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Should work here because we are logged in
        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.json()
        self._test_response_body(content)
        # 'self' should be a valid URL,
        # that when requested returns the same data we just received
        self_ = content["self"]["href"]
        assert uri_is_http(self_)
        self_res = self.client.get(self_)
        self.assertEqual(res.json(), self_res.json())

        # Request a user other than ourselves,
        # this should fail because we do not have permissions
        # to view users other than ourselves
        url = reverse(self.detail, args=(1,))
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test020_list(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to list all users
        THEN I should see all details of all users I can interact with
        (Note: This is currently only the user themselves)
        """
        url = reverse(self.list)

        # Should only work when we are logged in
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Should work here because we are logged in
        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.json()
        # Response body should be an array / list,
        # containing only one user - the logged in one
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 1)

    def test030_create(self):
        """
        GIVEN I am not logged in
        WHEN I ask to create a new user
            AND the email I rrequest is not already in use
        THEN I should be able to create a new user
        """
        url = reverse(self.list)

        # Should work even when we are not logged in
        # Here we create the most basic possible user,
        # we should get by here without specifying name at all
        user_data = self._test_user_data()
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        content = res.json()
        self._test_response_body(content)

        # Try and create a user with same email as above
        # This should fail as it does not pass the unique validation
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Create a user, while specifying literal 'None' for both names
        # This should work
        user_data = self._test_user_data()
        user_data["first_name"] = None
        user_data["last_name"] = None
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Create a user, while specifying only 'first_name'
        # This is expected to work
        FIRST_NAME_TEST = "Holger"
        user_data = self._test_user_data()
        user_data["first_name"] = FIRST_NAME_TEST
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        content = res.json()
        # The name should get returned in the 'last_name' attribute
        self.assertEqual(content["first_name"], FIRST_NAME_TEST)
        self.assertEqual(content["last_name"], None)

        # Attempt to create a user while specifying both
        # 'first_name' and 'last_name', this should work
        LAST_NAME_TEST = "Burgund"
        user_data = self._test_user_data()
        user_data["first_name"] = FIRST_NAME_TEST
        user_data["last_name"] = LAST_NAME_TEST
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        content = res.json()
        # This name should now be visible in the 'name' section
        self.assertEqual(content["first_name"], FIRST_NAME_TEST)
        self.assertEqual(content["last_name"], LAST_NAME_TEST)

        # Create a user while specifying only 'last_name'
        # This should work
        user_data = self._test_user_data()
        user_data["last_name"] = LAST_NAME_TEST
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        content = res.json()
        self.assertEqual(content["last_name"], LAST_NAME_TEST)

    def test040_profile_picture_upload(self):
        """
        GIVEN I am not logged in
        WHEN I ask to create a new user
            AND I provide a profile picture
            AND that profile picture is Base64 encoded
            AND the actual filesize is less than or equal to 200KB
            AND the image dimensions are exactly 192x192px
        THEN I should be able to create a new user
            AND save the profile picture for that user
        """
        url = reverse(self.list)

        # Create a test image
        image_file = generate_test_image("jpeg")
        b64_image = generate_image_b64(image_file)

        # Attempt to create a new user, this should work
        user_data = self._test_user_data()
        user_data["profile_picture"] = {
            "image": b64_image,
            "background": "#ffffff"
        }
        res = self.client.post(url, data=user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        content = res.json()
        new_user_id = self_to_id(content)
        User = get_user_model()
        new_user = User.objects.get(pk=new_user_id)

        # PATCH the profile picture back to None (effectively remove your profile picture)
        # This should work
        self.client.force_authenticate(user=new_user)
        url = reverse(self.detail, args=(new_user_id,))
        res = self.client.patch(url, data={
            "profile_picture": {
                "image": None
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.json()
        self.assertEqual(content["profile_picture"]["image"], None)

        # PATCH to a new profile picture with a different format
        # This should work
        res = self.client.patch(url, data={
            "profile_picture": {
                "image": IMG  # base64 as formatted by Frontend
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test050_update_general(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to update a user
            AND that user is myself
            AND I do not update 'email' or 'password'
        THEN I should be able to update an existing user
        """
        url = reverse(self.detail, args=(self.user.pk,))

        # Should only work when we are logged in, this will fail
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Attempt to update the email, this should not work
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(url, data={
            "email": "idkBrother@lmao.com"
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to update the password, this should not work
        res = self.client.patch(url, data={
            "password": "asadsinubxrgiubdrtiugn"
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to update the 'first_name' of a user
        # This should work
        FIRST_NAME_TEST = "Dieter"
        res = self.client.patch(url, data={
            "first_name": FIRST_NAME_TEST
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.json()
        self._test_response_body(content)
        self.assertEqual(content["first_name"], FIRST_NAME_TEST)

        # Update both name fields of the user to literal None
        # This should work in order to allow unsetting of names
        for name_field in ("first_name", "last_name"):
            res = self.client.patch(url, data={
                name_field: None
            })
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test060_update_email(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to update a users email
            AND that user is myself
            AND the password I specified matches my current password
            AND the email I specified is a valid email
            AND the email I specified is not already in use by another user
        THEN I should be able to update an existing users email
        """
        url = reverse(self.change_email, args=(self.user.pk,))

        # Should only work when we are logged in, this will fail
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Attempt to update our email while logged in
        # but without providing our password, this should fail
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(url, data={
            "new_email": "someMailOhyes@google.de"
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to update our email while logged in
        # but while providing a wrong password, this should fail
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(url, data={
            "new_email": "someMailOhyes@google.de",
            "password": "Okaysomepwthatswrong"
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to update our email while logged in
        # while providing the correct password, this should work
        EMAIL_TEST = "someMailOhyes@google.de"
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(url, data={
            "new_email": EMAIL_TEST,
            "password": self.user_pw
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.json()
        self._test_response_body(content)
        self.assertEqual(content["email"], EMAIL_TEST)

        # Make sure our email has actually been updated
        res = self.client.get(
            reverse(self.detail, args=(self.user.pk,))
        )
        self.assertEqual(res.json()["email"], EMAIL_TEST)

        # Attempt to update our email to something that is already in use
        # For that we first create a user and then attempt the update
        user_data = self._test_user_data()
        res = self.client.post(
            reverse(self.list), data=user_data
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        COMPARE_EMAIL = user_data.get("email")
        COMPARE_ID = self_to_id(res.json())
        COMPARE_PASSWORD = user_data.get("password")
        # Now attempt to update our own email to that users email
        # This should fail
        res = self.client.patch(url, data={
            "new_email": COMPARE_EMAIL,
            "password": self.user_pw
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to update the email for a user that is not ourselves
        # Even while providing valid credentials
        # this should fail with a 404, because currently users can only
        # see themselves so they will not find this user
        url = reverse(self.change_email, args=(COMPARE_ID,))
        res = self.client.patch(url, data={
            "new_email": "someDifferentEmaillol@okay.sw",
            "password": COMPARE_PASSWORD
        })
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test070_update_password(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to update a users password
            AND that user is myself
            AND the password I specified matches my current password
            AND the new password I specified passes password validation
        THEN I should be able to update an existing users password
        """
        url = reverse(self.change_password, args=(self.user.pk,))

        # Should only work when we are logged in, this will fail
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Attempt to update our password while logged in
        # but without providing the old password, this should fail
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(url, data={
            "new_password": "needAmedicBag"
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Only provide the correct, current password
        # This should also fail
        res = self.client.patch(url, data={
            "password": self.user_pw
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Provide our correct current password and a new one
        # This should work
        res = self.client.patch(url, data={
            "password": self.user_pw,
            "new_password": "ubsguzbuztrgbi"
        })
        self.assertEqual(res.status_code, status.HTTP_205_RESET_CONTENT)

        # Attempt to update the password for a user that is not ourselves
        # but while providing correct credentials
        # this should fail with a 404, because currently users can only
        # see themselves so they will not find this user
        # First create a user for this
        user_data = self._test_user_data()
        res = self.client.post(
            reverse(self.list), data=user_data
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        COMPARE_PASSWORD = user_data.get("password")
        COMPARE_ID = self_to_id(res.json())
        # Now attempt the update
        url = reverse(self.change_password, args=(COMPARE_ID,))
        res = self.client.patch(url, data={
            "password": COMPARE_PASSWORD,
            "new_password": "hbgjhbihgbihr"
        })
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test080_delete(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to delete a user
            AND that user is myself
            AND I supply my valid current password
        THEN I should be able to delete that user
        """
        url = reverse(self.detail, args=(self.user.id,))

        # Should only work when we are logged in, this will fail
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Attempt to delete our user but without providing a password.
        # This should fail.
        self.client.force_authenticate(user=self.user)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to delete our user but while providing an invalid password.
        # This should fail.
        res = self.client.delete(url, data={
            "password": "".join(
                random.choices(string.ascii_letters, k=16)
            )
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Delete the user while being logged in and providing a valid password
        # This should work.
        res = self.client.delete(url, data={
            "password": self.user_pw
        })
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
