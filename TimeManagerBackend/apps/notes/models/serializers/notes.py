from django.utils.timezone import now
from rest_framework import serializers

from TimeManagerBackend.lib.commons.constrained import VersionConstrainedUUIDField
from TimeManagerBackend.lib.commons.href import SelfHrefField
from TimeManagerBackend.lib.commons.defaults import CurrentUserPkDefault


class BoardNotesSerializer(serializers.Serializer):  # noqa abstract
    self = SelfHrefField(
        lookup_field="id",
        lookup_url_kwarg="pk",
        lookup_chain={"board": "parent.id"},
        read_only=True
    )
    id = VersionConstrainedUUIDField(uuid_version=4)

    last_edited = serializers.HiddenField(default=now, write_only=True)
    edited_by = serializers.HiddenField(
        default=CurrentUserPkDefault(), write_only=True
    )
    content = serializers.CharField(required=True, allow_blank=True)

    class Meta:
        self_view = "notes:board-note-detail"
        collection_name = ("notes__notes_board",)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class GroupNotesSerializer(BoardNotesSerializer):  # noqa abstract
    self = SelfHrefField(
        lookup_field="id",
        lookup_url_kwarg="pk",
        lookup_chain={"group": "parent.id", "board": "parent.parent.id"},
        read_only=True
    )

    class Meta:
        self_view = "notes:board-group-note-detail"
        collection_name = ("notes__notes_group",)


__all__ = ["BoardNotesSerializer", "GroupNotesSerializer"]
