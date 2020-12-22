from django.core.files.storage import default_storage
from django.db import models
from drf_extra_fields.fields import Base64ImageField
from drf_yasg import openapi
from storages.base import BaseStorage


class GooglePrivateImageField(models.ImageField):
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 upload_to="",
                 storage=None,
                 **kwargs) -> None:
        # If the user did not manually override the storage,
        # we construct a Storage with the acl option set to private.
        # Only do this if the storage class in use right now,
        # is a subclass of the BaseStorage of DjangoStorages.
        if storage is None:
            storage_cls = default_storage.__class__
            if issubclass(storage_cls, BaseStorage):
                # For the ACLs, see:
                # https://cloud.google.com/storage/docs/access-control/lists#predefined-acl
                storage = storage_cls(
                    default_acl="projectPrivate"
                )

        super(GooglePrivateImageField, self).__init__(
            verbose_name=verbose_name,
            name=name,
            upload_to=upload_to,
            storage=storage,
            **kwargs
        )


class GooglePublicImageField(models.ImageField):
    def __init__(self,
                 verbose_name=None,
                 name=None,
                 upload_to="",
                 storage=None,
                 **kwargs) -> None:
        if storage is None:
            storage_cls = default_storage.__class__
            if issubclass(storage_cls, BaseStorage):
                storage = storage_cls(
                    default_acl="publicRead",
                    querystring_auth=False
                )

        super(GooglePublicImageField, self).__init__(
            verbose_name=verbose_name,
            name=name,
            upload_to=upload_to,
            storage=storage,
            **kwargs
        )


class Base64HrefImageField(Base64ImageField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Image",
            "read_only": True,
            "properties": {
                "href": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_URI,
                    example="http://example.com/resource/1/"
                )
            }
        }

    def to_representation(self, value):
        val = super().to_representation(value)
        if not val:
            return None
        return {"href": value.url}
