from django.contrib.auth import get_user_model
from rest_framework import serializers

from TimeManagerBackend.apps.users.models.serializers import UserSerializer
from TimeManagerBackend.lib.commons.href import (
    SelfHrefField, DeferredCollectionField
)
from ..groups.serializers import NotesGroupListSerializer
from ..notes.serializers import BoardNotesSerializer


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
        self_view = "notes:boards-detail"


class BoardListMixin(serializers.Serializer):  # noqa
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


class BoardDetailMixin(serializers.Serializer):  # noqa
    notes = BoardNotesSerializer(many=True, read_only=True)
    groups = NotesGroupListSerializer(many=True, read_only=True)


# POST
class NotesBoardCreateSerializer(BoardDetailMixin, Board):  # noqa
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=get_user_model().objects.all(),
        allow_empty=True,
        required=False
    )
    owner = UserSerializer(
        default=serializers.CurrentUserDefault()
    )

    def create(self, validated_data):
        from ..models import NotesBoard
        members = validated_data.pop("members", [])
        members += [validated_data.get("owner")]

        board = NotesBoard.objects.create(**validated_data)
        board.members.set(members)
        board.save()

        return board

    def to_representation(self, instance):
        data = super().to_representation(instance)
        members = get_user_model().objects.filter(
            pk__in=data.pop("members", [])
        )
        data["members"] = UserSerializer(
            many=True, context=self.context
        ).to_representation(members)
        return data


# GET LIST
class NotesBoardListSerializer(BoardListMixin, Board):  # noqa
    class Meta:
        self_view = "notes:boards-detail"
        field_kwargs = {
            "members": {
                "many": True,
                "read_only": True
            }
        }


# GET DETAIL
# PATCH
# (DELETE)
class NotesBoardDetailSerializer(BoardDetailMixin, Board):  # noqa
    members = UserSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        if v := validated_data.get("title"):
            setattr(instance, "title", v)
        if v := validated_data.get("owner"):
            setattr(instance, "owner", v)

        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class NotesBoardMembersSerializer(serializers.Serializer):  # noqa
    members = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), required=True, many=True
    )


__all__ = [
    "NotesBoardCreateSerializer",
    "NotesBoardListSerializer",
    "NotesBoardDetailSerializer",
    "NotesBoardMembersSerializer"
]
