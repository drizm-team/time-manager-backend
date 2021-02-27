from drizm_django_commons.serializers import HexColorField
from rest_framework import serializers

from TimeManagerBackend.lib.commons.href import (
    SelfHrefField, DeferredCollectionField
)


class NotesGroupListSerializer(serializers.Serializer):  # noqa
    self = SelfHrefField()

    title = serializers.CharField()
    color = HexColorField()

    notes = DeferredCollectionField(
        queryset_source="notes",
        view_name="notes:boards-detail",
        lookup_field="id", lookup_url_kwarg="pk",
        read_only=True
    )

    class Meta:
        self_view = "notes:board-groups-detail"


class NotesGroupDetailSerializer(NotesGroupListSerializer):  # noqa
    # notes = GroupNotesSerializer(many=True)
    pass


__all__ = ["NotesGroupListSerializer", "NotesGroupDetailSerializer"]
