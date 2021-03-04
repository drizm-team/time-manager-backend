from django.db import models

from TimeManagerBackend.lib.commons.firestore import get_firestore


class NotesGroup(models.Model):
    title = models.CharField(max_length=50)
    color = models.IntegerField()

    parent = models.ForeignKey(
        to="notes.NotesBoard",
        on_delete=models.CASCADE,
        related_name="groups"
    )

    class Meta:
        indexes = [
            models.Index(fields=["parent"])
        ]

    @property
    def notes(self):
        db = get_firestore()
        col_ref = db.collection(
            "notes__boards", str(self.parent.pk), "groups", str(self.pk), "notes"
        )
        return list(col_ref.list_documents())  # resolve the iterator


__all__ = ["NotesGroup"]
