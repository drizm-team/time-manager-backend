from typing import Union


class CurrentUserPkDefault:
    requires_context = True

    def __call__(self, serializer_field) -> Union[str, int]:
        return serializer_field.context["request"].user.pk

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__
