from django.db import models


class Event(models.Model):
    creator = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)
    primary_color = models.IntegerField()
    secondary_color = models.IntegerField()

    start = models.DateTimeField()
    end = models.DateTimeField(null=True)
    all_day = models.BooleanField(default=False)


__all__ = ["Event"]
