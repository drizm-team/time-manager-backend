from django.db import models


class NotesGroup(models.Model):
    title = models.CharField(max_length=50)
    color = models.IntegerField()

    parent = models.ForeignKey(
        to="notes.NotesBoard",
        on_delete=models.CASCADE,
        related_name="groups"
    )
    # notes - on manager side

    class Meta:
        indexes = [
            models.Index(fields=["parent"])
        ]


__all__ = ["NotesGroup"]
