from drizm_django_commons.files.validators import MaxFileSizeValidator
from drizm_django_commons.images.validators import ExactImageDimensionsValidator
from drizm_django_commons.serializers.fields import HexColorField
from rest_framework import serializers

from .fields import Base64HrefImageField
from .models import UserProfilePicture


class UserProfilePictureSerializer(serializers.ModelSerializer):
    image = Base64HrefImageField(
        required=False,
        validators=[
            ExactImageDimensionsValidator(
                x=192, y=192
            ),
            MaxFileSizeValidator(max_size_bytes=200000)  # 200KB
        ],
        allow_null=True,
    )
    background = HexColorField(required=True)

    class Meta:
        model = UserProfilePicture
        fields = ("image", "background")
