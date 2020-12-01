from drizm_django_commons.serializers import HrefModelSerializer
from drizm_django_commons.serializers.fields import SelfHrefField

from rest_framework import serializers
from .models import Note
from drizm_commons.utils import uuid4_is_valid


class NotesSerializer(HrefModelSerializer):
    id = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        self_view = "notes:note-detail"
        model = Note
        exclude = ["created"]
        extra_kwargs = {
            "creator": {
                "default": serializers.CurrentUserDefault(),
                "write_only": True
            },
            "content": {
                "required": False,
                "allow_blank": True
            }
        }

    # noinspection PyMethodMayBeStatic
    def validate_pk(self, value: str) -> str:
        if not uuid4_is_valid(value):
            raise serializers.ValidationError("Invalid UUIDv4")
        return value


class NotesResponseSchema(serializers.Serializer):  # noqa must implement abstract
    self = SelfHrefField(view_name="notes:note-detail")
    content = serializers.CharField()


class NotesRequestSchema(serializers.Serializer):  # noqa must implement abstract
    content = serializers.CharField()
