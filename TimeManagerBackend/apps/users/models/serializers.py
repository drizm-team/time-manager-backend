from django.contrib.auth import get_user_model
from drizm_django_commons.serializers.fields import SelfHrefField
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator


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

    def create(self, validated_data):
        model = get_user_model()
        return model.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        instance.password = validated_data.get("password", instance.password)
        instance.save()
        return instance


class EmailTokenObtainSerializer(  # noqa must implement abstract
    TokenObtainSerializer
):
    username_field = get_user_model().EMAIL_FIELD


class CustomTokenObtainPairSerializer(  # noqa must implement abstract
    EmailTokenObtainSerializer
):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        return data


class ObtainSchema(serializers.Serializer):  # noqa must implement abstract
    access = serializers.CharField(required=True)
    refresh = serializers.CharField(required=True)


class RefreshSchema(serializers.Serializer):  # noqa must implement abstract
    access = serializers.CharField(required=True)


class UserResponseSchema(serializers.Serializer):  # noqa must implement abstract
    self = SelfHrefField(
        lookup_field="pk",
        view_name="users:user-detail"
    )
    email = serializers.EmailField()
