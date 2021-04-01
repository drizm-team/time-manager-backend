from django.db import models
from google.cloud import firestore

from TimeManagerBackend.lib.commons.firestore import (
    get_firestore, DocumentWrapper
)


class NotesGroup(models.Model):
    title = models.CharField(max_length=50)
    color = models.IntegerField()

    parent = models.ForeignKey(
        to="notes.NotesBoard",
        on_delete=models.CASCADE,
        related_name="groups"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["parent"])
        ]
        ordering = ["created"]

    @property
    def notes(self):
        db = get_firestore()
        col_query = db.collection(
            "notes__groups", str(self.pk), "notes"
        ).order_by(
            "created", direction=firestore.Query.DESCENDING
        ).stream()
        return [DocumentWrapper(d) for d in col_query]


__all__ = ["NotesGroup"]
