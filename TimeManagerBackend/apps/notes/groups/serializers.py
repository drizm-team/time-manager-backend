from drizm_django_commons.serializers import HexColorField
from rest_framework import serializers

from TimeManagerBackend.lib.commons.href import (
    SelfHrefField, DeferredCollectionField
)
from .models import NotesGroup
from ..boards.models import NotesBoard
from ..notes.serializers import GroupNotesSerializer


# POST
# GET LIST
class NotesGroupListSerializer(serializers.Serializer):  # noqa
    self = SelfHrefField(
        view_name="notes:groups-detail",
        lookup_chain={"boards_pk": "parent.pk"}
    )

    title = serializers.CharField(required=True)
    color = HexColorField(required=True)

    parent = serializers.PrimaryKeyRelatedField(
        queryset=NotesBoard.objects.all(),
        write_only=True,
        required=True
    )
    notes = DeferredCollectionField(
        queryset_source="notes",
        view_name="notes:boards-detail",
        lookup_field="id", lookup_url_kwarg="pk",
        read_only=True
    )


class NotesGroupDetailSerializer(NotesGroupListSerializer):  # noqa
    notes = GroupNotesSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return NotesGroup.objects.create(**validated_data)

    def update(self, instance, validated_data: dict):
        allowed_attrs = ("title", "color")
        for attr in allowed_attrs:
            if v := validated_data.pop(attr, None):
                setattr(instance, attr, v)

        instance.save()
        return instance


__all__ = ["NotesGroupListSerializer", "NotesGroupDetailSerializer"]
