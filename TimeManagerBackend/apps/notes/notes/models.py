from django.utils.timezone import now
from rest_framework import serializers

from TimeManagerBackend.lib.commons.constrained import VersionConstrainedUUIDField


class Note(serializers.Serializer):  # noqa abstract
    id = VersionConstrainedUUIDField(uuid_version=4)

    created = serializers.HiddenField(default=now, write_only=True)
    creator = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), write_only=True
    )
    content = serializers.CharField(required=False, allow_blank=True)


__all__ = ["Note"]
