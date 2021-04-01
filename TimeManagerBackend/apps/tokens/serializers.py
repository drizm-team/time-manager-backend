from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken


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


class TokenDestroySchema(serializers.Serializer):  # noqa must implement abstract
    refresh = serializers.CharField(required=True)
