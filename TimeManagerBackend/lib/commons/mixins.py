from typing import Type

from rest_framework.serializers import Serializer


class SerializerContextMixin:
    serializer_class: Type[Serializer]

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method." % self.__class__.__name__
        )

        return self.serializer_class

    def get_serializer_context(self) -> dict:
        return {
            "request": self.request,  # noqa mixin
            "format": self.format_kwarg,  # noqa mixin
            "view": self,
        }


__all__ = ["SerializerContextMixin"]
