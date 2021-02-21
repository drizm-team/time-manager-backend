import operator
from operator import attrgetter
from typing import Union, Sequence, List, Dict, Optional, Any, Callable
from urllib.parse import quote_plus, urljoin

from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.urls import NoReverseMatch
from drf_yasg import openapi
from rest_framework import serializers
from rest_framework.relations import Hyperlink


class HrefField(serializers.HyperlinkedIdentityField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Href",
            "read_only": True,
            "properties": {
                "href": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_URI,
                    example="http://example.com/resource/1/",
                )
            },
        }

    def __init__(
        self,
        lookup_chain: Optional[Dict[str, Union[str, Callable]]] = None,
        referring_field: Optional[str] = None,
        **kwargs,
    ) -> None:
        super(HrefField, self).__init__(**kwargs)

        if lookup_chain and len(lookup_chain) > 3:
            raise ValueError(
                "For performance reasons, the lookup chain of a single "
                "object, may not be longer than 3 lookups."
            )
        self.lookup_chain = lookup_chain

        self.referring_field = referring_field

    # noinspection PyMethodMayBeStatic
    def attach_fragment(self, url, fragment: str) -> str:
        return urljoin(url, "#" + quote_plus(fragment))

    def get_url(self, obj, view_name, request, format_):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None

        # Default lookup resolve
        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}

        # Resolve the lookup chain by retrieving the attributes from our object
        if self.lookup_chain:
            for kwarg, lookup in self.lookup_chain.items():
                if callable(lookup):
                    kwargs[kwarg] = lookup(obj)
                else:
                    kwargs[kwarg] = operator.attrgetter(lookup)(obj)

        url = self.reverse(view_name, kwargs=kwargs, request=request, format=format_)
        if self.referring_field:
            url = self.attach_fragment(url, self.referring_field)

        return url

    def _get_url_representation(
        self, value: Any, view_name: Optional[str] = None
    ) -> Optional[str]:
        """ Copied from base with a few adjustments for Viewname detection """
        assert "request" in self.context, (
            "`%s` requires the request in the serializer"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer." % self.__class__.__name__
        )

        request = self.context.get("request")
        format_ = self.context.get("format", None)

        if format_ and self.format and self.format != format_:
            format_ = self.format

        try:
            reverse_view = view_name or self.view_name
            url = self.get_url(value, reverse_view, request, format_)

        except NoReverseMatch:
            msg = (
                "Could not resolve URL for hyperlinked relationship using "
                "view name '%s'. You may have failed to include the related "
                "model in your API, or incorrectly configured the "
                "`lookup_field` attribute on this field."
            )
            if value in ("", None):
                value_string = {"": "the empty string", None: "None"}[value]
                msg += (
                    " WARNING: The value of the field on the model instance "
                    "was %s, which may be why it didn't match any "
                    "entries in your URL conf." % value_string
                )
            raise ImproperlyConfigured(msg % self.view_name)

        if url is None:
            return None

        return Hyperlink(url, value)

    def to_representation(self, value) -> Dict[str, str]:
        """ Wrap the default hyperlink representation in a href object. """
        url = self._get_url_representation(value, self.view_name)
        return {"href": url}


class SelfHrefField(HrefField):
    def __init__(
        self, view_name: str = "nil", lookup_chain=None, referring_field=None, **kwargs
    ) -> None:
        kwargs["view_name"] = view_name
        super(SelfHrefField, self).__init__(lookup_chain, referring_field, **kwargs)

    def to_representation(self, value) -> Dict[str, str]:
        if not (self.view_name and self.view_name not in ("nil", "", None)):
            if hasattr(self.parent, "Meta"):
                if v := getattr(self.parent.Meta, "self_view", False):
                    self.view_name = v

        return super(SelfHrefField, self).to_representation(value)


class DeferredCollectionField(HrefField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_ARRAY,
            "title": "Href Collection",
            "read_only": True,
            "properties": {
                "href": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_URI,
                    example="http://example.com/resource/1/",
                ),
                "count": openapi.Schema(
                    type=openapi.TYPE_INTEGER, format=openapi.FORMAT_INT32, example=7
                ),
            },
        }

    def __init__(
        self,
        queryset: Optional[Union[Sequence, QuerySet]] = None,
        queryset_source: Optional[str] = None,
        lookup_chain=None,
        lookup_field=None,
        referring_field=None,
        **kwargs,
    ) -> None:
        if queryset and queryset_source:
            raise ValueError(
                "The 'queryset' and 'queryset_source' parameters, "
                "are exclusive to one another, please specify only one "
                "of the two parameters."
            )

        if not queryset and not queryset_source:
            raise ValueError(
                "You must provide either the 'queryset' or "
                "'queryset_source' parameters to this field."
            )

        kwargs["lookup_field"] = lookup_field
        super(DeferredCollectionField, self).__init__(
            lookup_chain, referring_field, **kwargs
        )

        self.queryset_setting = queryset

    def evaluate_queryset_length(self, obj, qset=None):
        q = qset or self.queryset_setting

        if isinstance(q, QuerySet):
            length = q.count()
        elif isinstance(q, Sequence):
            length = len(q)
        elif isinstance(q, str):
            q = attrgetter(q)(obj)
            return self.evaluate_queryset_length(obj, qset=q)
        else:
            raise TypeError("Not a valid Queryset.")

        return length  # noqa ref before assignment

    def get_url(self, obj, view_name, request, format_):
        if not self.lookup_field and not self.lookup_chain:
            url = self.reverse(view_name, request=request, format=format_)
            if self.referring_field:
                url = self.attach_fragment(url, self.referring_field)

            return url

        return super().get_url(obj, view_name, request, format_)

    def to_representation(self, value) -> List[Dict[str, str]]:
        href = super().to_representation(value)

        return [{
            **href,
            "count": self.evaluate_queryset_length(value)
        }]


__all__ = ["HrefField", "SelfHrefField", "DeferredCollectionField"]
