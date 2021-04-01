import random
import string

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from storages.backends.gcloud import GoogleCloudStorage

from TimeManagerBackend.apps.images.models import UserProfilePicture
from ..conftest import (
    generate_test_image,
    create_test_user,
    random_hex_color,
    generate_image_b64
)


class TestImages(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.detail = "users:user-detail"

        cls._storage: GoogleCloudStorage = default_storage
        cls.storage = cls._storage.client

        super().setUpClass()

    def setUp(self) -> None:
        self.user = create_test_user()
        self.url = reverse(self.detail, args=(self.user.id,))

    # noinspection PyMethodMayBeStatic
    def _test_user_data(self) -> dict:
        email = (
            f"{''.join(random.choices(string.ascii_letters, k=8))}"
            "@tester.de"
        )
        return {
            "email": email,
            "password": "somePasswordIdc",
            "profile_picture": {
                "background": random_hex_color()
            }
        }

    # noinspection PyMethodMayBeStatic
    def _test_image(self):
        image_bytes = generate_test_image("jpeg")
        return generate_image_b64(image_bytes)

    def test010_cascade_delete_images(self):
        """
        GIVEN I have a user object with a profile picture
        WHEN I delete that user
        THEN the user object and the profile picture should be deleted
            AND the image saved to GCS should also be deleted
        """
        # Create a new profile picture and assign it to the user.
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(self.url, data={
            "profile_picture": {
                "image": self._test_image()
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check that only one UserProfilePicture object exists right now.
        # This should be the case.
        profile_pictures = UserProfilePicture.objects.all()
        self.assertEqual(
            len(profile_pictures), 1
        )

        # Check that only one image (blob) exists in the storage bucket right now
        # This should be the image from the UserProfilePicture object
        # that we created previously.
        # This should pass.
        blobs = list(
            self.storage.list_blobs(settings.GS_BUCKET_NAME)
        )
        self.assertEqual(
            len(blobs), 1
        )

        # Delete the user and now check that the UserProfilePicture object
        # and its related image, that has been saved to GCS, also get deleted.
        # This should be the case.
        self.user.delete()

        profile_pictures = UserProfilePicture.objects.all()
        self.assertEqual(
            len(profile_pictures), 0
        )

        blobs = list(
            self.storage.list_blobs(settings.GS_BUCKET_NAME)
        )
        self.assertEqual(
            len(blobs), 0
        )

    def test020_remove_image(self):
        """
        GIVEN I have a user object with a profile picture
        WHEN I update the profile picture of the user to None
        THEN the profile picture image, saved to GCS, should be deleted
        """
        # Create a test image and assign it to the user
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(self.url, data={
            "profile_picture": {
                "image": self._test_image()
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # With the users new profile picture uploaded,
        # we should now have one blob in the storage bucket
        blobs = list(
            self.storage.list_blobs(settings.GS_BUCKET_NAME)
        )
        self.assertEqual(
            len(blobs), 1
        )

        # PATCH the new users profile picture to None
        # This should work and also delete the image in GCS
        res = self.client.patch(self.url, data={
            "profile_picture": {
                "image": None
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # The image should be deleted from GCS after being updated to None
        blobs = list(
            self.storage.list_blobs(settings.GS_BUCKET_NAME)
        )
        self.assertEqual(
            len(blobs), 0
        )

    def test030_overwrite_image(self):
        """
        GIVEN I have a user object with a profile picture
        WHEN I update the profile picture of the user
        THEN the old profile picture image, saved to GCS, should be deleted
            AND the new profile picture image should be saved under the same name
        """
        # Create a test image and assign it to the user
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(self.url, data={
            "profile_picture": {
                "image": self._test_image()
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Again, check that the new profile picture has been properly uploaded
        blobs = list(
            self.storage.list_blobs(settings.GS_BUCKET_NAME)
        )
        self.assertEqual(
            len(blobs), 1
        )

        # Extract the new users data
        content = res.json()
        profile_picture_url = content["profile_picture"]["image"].get("href")

        # Update the new users profile picture to a new image
        # This should work and also delete the old image from GCS,
        # the new image should however still be available under the same URL,
        # since the name of the file has not changed
        res = self.client.patch(self.url, data={
            "profile_picture": {
                "image": self._test_image()
            }
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        content = res.json()
        self.assertEqual(
            profile_picture_url,
            content["profile_picture"]["image"].get("href")
        )
        blobs = list(
            self.storage.list_blobs(settings.GS_BUCKET_NAME)
        )
        self.assertEqual(
            len(blobs), 1
        )
