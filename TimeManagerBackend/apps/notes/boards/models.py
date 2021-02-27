from django.contrib.auth import get_user_model
from django.db import models

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
        col_ref = db.collection("notes__boards", str(self.pk), "notes")
        return list(col_ref.list_documents())  # resolve the iterator


__all__ = ["NotesBoard"]
