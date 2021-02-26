from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now
from rest_framework import serializers

from TimeManagerBackend.lib.commons.constrained import VersionConstrainedUUIDField
from TimeManagerBackend.lib.commons.firestore import get_firestore


class NotesBoard(models.Model):
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="owned_boards"
    )
    # The owner will also be a member
    members = models.ManyToManyField(to=get_user_model())
    # groups - on groups side
    # notes - on manager side

    @property
    def notes(self):
        db = get_firestore()
        col_ref = db.collection("notes__boards", self.pk, "notes")
        return col_ref.all()


class NotesGroup(models.Model):
    title = models.CharField(max_length=50)
    color = models.IntegerField()

    parent = models.ForeignKey(
        to=NotesBoard,
        on_delete=models.CASCADE,
        related_name="groups"
    )
    # notes - on manager side

    class Meta:
        indexes = [
            models.Index(fields=["parent"])
        ]


class Note(serializers.Serializer):  # noqa abstract
    id = VersionConstrainedUUIDField(uuid_version=4)

    created = serializers.HiddenField(default=now, write_only=True)
    creator = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), write_only=True
    )
    content = serializers.CharField(required=False, allow_blank=True)


__all__ = ["Note", "NotesBoard", "NotesGroup"]
