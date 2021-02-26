from django.contrib.auth import get_user_model
from rest_framework import serializers

from TimeManagerBackend.apps.users.models.serializers import UserSerializer
from TimeManagerBackend.lib.commons.href import (
    SelfHrefField, DeferredCollectionField
)
from .groups import NotesGroupListSerializer
from .notes import BoardNotesSerializer


class Board(serializers.Serializer):  # noqa
    self = SelfHrefField(
        lookup_field="id", lookup_url_kwarg="pk", read_only=True
    )
    title = serializers.CharField(
        required=True, min_length=2, max_length=100
    )
    owner = UserSerializer()
    members = UserSerializer(many=True)
    # notes
    # groups

    class Meta:
        self_view = "notes:note-boards-detail"

    def validate(self, attrs: dict):
        # The owner cannot be a member at the same time
        owner, members = attrs.get("owner"), attrs.get("members")
        if owner in members:
            raise serializers.ValidationError


class BoardListMixin:
    notes = DeferredCollectionField(
        queryset_source="notes",
        view_name="notes:boards-detail",
        lookup_field="id", lookup_url_kwarg="pk",
        referring_field="notes",
        read_only=True
    )
    groups = DeferredCollectionField(
        queryset_source="groups",
        view_name="notes:boards-detail",
        lookup_field="id", lookup_url_kwarg="pk",
        referring_field="groups",
        read_only=True
    )


class BoardDetailMixin:
    notes = BoardNotesSerializer(many=True, read_only=True)
    groups = NotesGroupListSerializer(many=True, read_only=True)


class NotesBoardCreateSerializer(BoardListMixin, Board):  # noqa
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=get_user_model().objects.all(),
        allow_empty=True
    )

    class Meta:
        field_kwargs = {
            "owner": {
                "default": serializers.CurrentUserDefault(),
                "read_only": True
            },
        }

    def create(self, validated_data):
        from ..models import NotesBoard

        return NotesBoard.objects.create(**validated_data)


class NotesBoardListSerializer(BoardListMixin, Board):  # noqa
    class Meta:
        field_kwargs = {
            "members": {
                "many": True,
                "read_only": True
            }
        }


class NotesBoardDetailSerializer(BoardDetailMixin, Board):  # noqa
    class Meta:
        field_kwargs = {
            "members": {
                "many": True,
                "read_only": True
            }
        }

    def update(self, instance, validated_data):
        if v := validated_data.get("title"):
            setattr(instance, "title", v)
        if v := validated_data.get("owner"):
            setattr(instance, "owner", v)

        instance.save()
        return instance


__all__ = [
    "NotesBoardCreateSerializer",
    "NotesBoardListSerializer",
    "NotesBoardDetailSerializer"
]
