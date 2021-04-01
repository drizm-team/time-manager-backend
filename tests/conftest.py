import base64
import io
import random
from typing import Dict, Tuple, Optional

from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from TimeManagerBackend.apps.images.models.serializers import UserProfilePictureSerializer

# Default set of credentials for the test user
TEST_USER_EMAIL = "default_tester@tester.de"
TEST_USER_PASSWORD = "shittySecurity420!"


def create_test_user(email: Optional[str] = None,
                     password: Optional[str] = None):
    serializer = UserProfilePictureSerializer(data={
        "background": random_hex_color()
    })
    serializer.is_valid(raise_exception=True)
    profile_picture = serializer.save()

    User = get_user_model()
    user = User.objects.create_user(
        email=email or TEST_USER_EMAIL,
        password=password or TEST_USER_PASSWORD,
        profile_picture=profile_picture
    )
    profile_picture.save()
    return user


def obtain_tokens(cls: APITestCase,
                  credentials: Dict[str, str]
                  ) -> Tuple[str, str, Response]:
    """ Attempts to obtain a token pair for a set of credentials """
    url = reverse("tokens:obtain_delete")
    res = cls.client.post(url, data=credentials)
    if not res.status_code == status.HTTP_200_OK:
        raise ValueError(
            "Credentials invalid"
        )

    content = res.json()
    access_token = content.get("access")
    refresh_token = content.get("refresh")
    return access_token, refresh_token, res


def self_to_id(body: dict):
    identifier = [
        i for i in body["self"].get("href").split("/") if i
    ][-1]
    try:
        identifier = int(identifier)
    except TypeError:
        pass
    finally:
        return identifier


def generate_test_image(ext: Optional[str] = "jpeg") -> io.BytesIO:
    file = io.BytesIO()
    image = Image.new(
        "RGB",
        size=(192, 192),
        color=tuple(  # generate a random color
            random.randint(100, 200) for _ in range(3)
        )
    )
    image.save(file, ext)

    return file


def generate_image_b64(image_file: io.BytesIO) -> bytes:
    return base64.b64encode(image_file.getvalue())


def random_hex_color() -> str:
    return "#%06x" % random.randint(0, 0xFFFFFF)


__all__ = [
    "TEST_USER_EMAIL", "TEST_USER_PASSWORD",
    "create_test_user", "obtain_tokens", "self_to_id",
    "generate_test_image", "generate_image_b64", "random_hex_color"
]
