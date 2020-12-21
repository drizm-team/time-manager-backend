from django.contrib.auth import get_user_model
from drizm_django_commons.serializers import SelfHrefField
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.validators import UniqueValidator

from TimeManagerBackend.apps.images.models import UserProfilePicture
from TimeManagerBackend.apps.images.models.serializers import UserProfilePictureSerializer


class UserSerializer(serializers.Serializer):
    self = SelfHrefField(
        lookup_field="pk",
        view_name="users:user-detail"
    )
    email = serializers.EmailField(
        required=True, validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all()
            )
        ]
    )
    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        required=True
    )
    first_name = serializers.CharField(
        min_length=2,
        max_length=150,
        required=False,
    )
    last_name = serializers.CharField(
        min_length=2,
        max_length=150,
        required=False,
    )
    profile_picture = UserProfilePictureSerializer(required=True)

    def create(self, validated_data):
        profile_picture_data = validated_data.pop("profile_picture")
        profile_picture = UserProfilePicture.objects.create(
            **profile_picture_data
        )
        validated_data["profile_picture"] = profile_picture

        # Obtain and construct the model instance
        User = get_user_model()
        user = User.objects.create_user(**validated_data)

        # The OneToOneField reverse accessor is not symmetrical
        # So we need to also save the other instance
        # for the changes to be reflected on both sides
        profile_picture.save()

        return user

    def update(self, instance, validated_data):
        if validated_data.get("profile_picture"):
            profile_picture_data = validated_data.pop("profile_picture")

            for k, v in profile_picture_data.items():
                setattr(instance.profile_picture, k, v)

            instance.save()

            # The OneToOneField reverse accessor is not symmetrical
            # So we need to also save the other instance
            # for the changes to be reflected on both sides
            instance.profile_picture.save()

        if "password" in validated_data:
            new_password = validated_data.pop("password")
            instance.set_password(new_password)

        for field_name, value in validated_data.items():
            setattr(
                instance,
                field_name,
                value
            )

        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get("first_name"):
            data["first_name"] = None
        if not data.get("last_name"):
            data["last_name"] = None
        return data


class CurrentPasswordRequiredSerializer(serializers.Serializer):  # noqa must implement abstract
    password = serializers.CharField(required=True)

    def validate_password(self, value):
        request: Request = self.context.get("request")
        user = request.user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Provided password is incorrect."
            )
        return value


class PasswordChangeSerializer(CurrentPasswordRequiredSerializer):  # noqa must implement abstract
    new_password = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        instance.set_password(
            validated_data.get("new_password")
        )
        instance.save()
        return instance


class EmailChangeSerializer(CurrentPasswordRequiredSerializer):  # noqa must implement abstract
    new_email = serializers.EmailField(
        required=True,
        source="email",
        validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all()
            )
        ]
    )

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email")
        instance.save()
        return instance
