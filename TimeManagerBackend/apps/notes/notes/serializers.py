from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import serializers

from TimeManagerBackend.apps.users.models.serializers import UserSerializer
from TimeManagerBackend.lib.commons.constrained import VersionConstrainedUUIDField
from TimeManagerBackend.lib.commons.defaults import CurrentUserPkDefault
from TimeManagerBackend.lib.commons.firestore import get_firestore, DocumentWrapper
from TimeManagerBackend.lib.commons.href import SelfHrefField
from ..boards.models import NotesBoard
from ..groups.models import NotesGroup


class NotesSerializerMixin:
    def to_representation(self, instance):
        self_ = self.fields.get(  # noqa mixin
            "self"
        ).to_representation(instance)
        content = instance.content
        edited_by = UserSerializer(
            get_user_model().objects.get(id=instance.edited_by),
            context=self.context  # noqa mixin
        ).data
        last_edited = serializers.DateTimeField().to_representation(
            instance.last_edited
        )
        return {
            "self": self_,
            "content": content,
            "edited_by": edited_by,
            "last_edited": last_edited
        }

    # noinspection PyMethodMayBeStatic
    def update(self, instance, validated_data):
        instance.reference.set({
            "last_edited": validated_data.pop("last_edited"),
            "edited_by": validated_data.pop("edited_by"),
            "content": validated_data.pop("content")
        }, merge=True)

        return DocumentWrapper(instance.reference.get())

    def create(self, validated_data):
        db = get_firestore()
        pk = str(validated_data.pop("id"))
        parent_pk = validated_data.pop("parent").pk

        col_ref = db.collection(
            self.Meta.collection_name, str(parent_pk), "notes"  # noqa mixin
        )
        doc_ref = col_ref.document(pk)
        doc_ref.set(validated_data)
        return DocumentWrapper(doc_ref.get())


class BoardNotesSerializer(NotesSerializerMixin, serializers.Serializer):
    self = SelfHrefField(
        lookup_field="id",
        lookup_url_kwarg="pk",
        lookup_chain={"boards_pk": "reference.parent.parent.id"},
        read_only=True
    )
    id = VersionConstrainedUUIDField(
        uuid_version=4, write_only=True, required=True
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=NotesBoard.objects.all()
    )

    created = serializers.HiddenField(default=now)
    last_edited = serializers.HiddenField(default=now)
    edited_by = serializers.HiddenField(default=CurrentUserPkDefault())
    content = serializers.CharField(required=True, allow_blank=True)

    class Meta:
        self_view = "notes:boards-notes"
        collection_name = "notes__boards"


def get_boards_pk(obj):
    parent_id = obj.reference.parent.parent.id
    group = NotesGroup.objects.get(id=parent_id)
    return group.parent_id


class GroupNotesSerializer(NotesSerializerMixin, serializers.Serializer):
    self = SelfHrefField(
        lookup_field="id",
        lookup_url_kwarg="pk",
        lookup_chain={
            "boards_pk": get_boards_pk,
            "groups_pk": "reference.parent.parent.id"
        },
        read_only=True
    )
    id = VersionConstrainedUUIDField(
        uuid_version=4, write_only=True, required=True
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=NotesGroup.objects.all()
    )

    created = serializers.HiddenField(default=now)
    last_edited = serializers.HiddenField(default=now)
    edited_by = serializers.HiddenField(default=CurrentUserPkDefault())
    content = serializers.CharField(required=True, allow_blank=True)

    class Meta:
        self_view = "notes:groups-notes"
        collection_name = "notes__groups"


__all__ = [
    "BoardNotesSerializer", "GroupNotesSerializer"
]
