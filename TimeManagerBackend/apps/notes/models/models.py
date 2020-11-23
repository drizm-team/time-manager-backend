from django.contrib.auth import get_user_model
from django.db import models


class Note(models.Model):
    id = models.UUIDField(primary_key=True)
    creator = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )
    content = models.TextField(null=True)

    class Meta:
        ordering = ("-created",)


__all__ = ["Note"]
