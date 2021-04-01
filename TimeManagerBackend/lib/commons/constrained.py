import uuid

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class VersionConstrainedUUIDField(serializers.Field):
    valid_formats = ("hex_verbose", "hex", "int", "urn")
    valid_versions = (4, 5, 6)

    default_error_messages = {
        "invalid": _("Must be a valid UUID of version {version}.")
    }

    def __init__(self, **kwargs) -> None:
        self.uuid_version: int = kwargs.pop("uuid_version", 4)
        if self.uuid_version not in self.valid_versions:
            raise ValueError(
                "Invalid UUID version provided. "
                "Must be one of '{}'".format(
                    '", "'.join(
                        map(lambda v: str(v), self.valid_versions)
                    )
                )
            )

        self.uuid_format = kwargs.pop("format", "hex_verbose")
        if self.uuid_format not in self.valid_formats:
            raise ValueError(
                "Invalid format for uuid representation. "
                "Must be one of '{}'".format('", "'.join(self.valid_formats))
            )

        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if not isinstance(data, uuid.UUID):
            try:
                if isinstance(data, int):
                    return uuid.UUID(int=data, version=self.uuid_version)
                elif isinstance(data, str):
                    return uuid.UUID(hex=data, version=self.uuid_version)
                else:
                    self.fail("invalid", version=self.uuid_version)
            except ValueError:
                self.fail("invalid", version=self.uuid_version)
        return data

    def to_representation(self, value):
        if self.uuid_format == "hex_verbose":
            return str(value)
        else:
            return getattr(value, self.uuid_format)
