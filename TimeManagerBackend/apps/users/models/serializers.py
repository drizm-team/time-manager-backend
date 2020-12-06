from django.contrib.auth import get_user_model
from drizm_django_commons.serializers import SelfHrefField
from rest_framework import serializers
from rest_framework.request import Request
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
        max_length=50,
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

    def create(self, validated_data):
        # Obtain and construct the model instance
        model = get_user_model()
        return model.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
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
