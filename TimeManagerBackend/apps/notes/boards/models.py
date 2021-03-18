from django.contrib.auth import get_user_model
from django.db import models

from TimeManagerBackend.lib.commons.firestore import (
    get_firestore, DocumentWrapper
)


class NotesBoard(models.Model):
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="owned_boards"
    )
    # The owner will also be a member
    members = models.ManyToManyField(to=get_user_model())
    created = models.DateTimeField(auto_now_add=True)
    # groups - on groups side

    @property
    def notes(self):
        db = get_firestore()
        col_ref = db.collection("notes__boards", str(self.pk), "notes")
        return [DocumentWrapper(d) for d in col_ref.list_documents()]

    class Meta:
        ordering = ["created"]


__all__ = ["NotesBoard"]
