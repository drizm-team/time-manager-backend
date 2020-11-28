from copy import deepcopy
from typing import Optional

import google.auth.transport.requests
from django.conf import settings
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header
)
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from TimeManagerBackend.apps.errors.errors import NotAuthenticatedException


class _ServiceAccountIDTokenAuth(BaseAuthentication):
    strict = False

    def authenticate(self, request: Request) -> tuple:
        auth = get_authorization_header(request).decode()
        try:
            scheme, token = auth.split()
        except ValueError:
            exc = NotAuthenticatedException("Invalid Header.")
            exc.status_code = 401
            raise exc
        if not scheme == "Bearer":
            raise NotAuthenticatedException("Invalid scheme.")

        try:
            req = google.auth.transport.requests.Request()
            payload = id_token.verify_token(
                token, request=req
            )
            sub = payload["sub"]
            audience = payload["aud"]
        except KeyError:
            raise NotAuthenticatedException("Invalid validation payload.")
        except Exception:  # noqa E722
            raise NotAuthenticatedException("Invalid token.")

        if self.strict:
            from urllib.parse import urlparse
            request_result = urlparse(
                request._request.build_absolute_uri()  # noqa protected
            )
            audience_result = urlparse(audience)

            server_domain = request_result.netloc
            audience_domain = audience_result.netloc

            if audience_domain not in server_domain:
                raise NotAuthenticatedException("Invalid audience.")

        User = get_user_model()
        user = User.objects.filter(sub=sub).first()
        if not user or not user.is_active:
            raise NotAuthenticatedException("Invalid token.")

        return user, None


def ServiceAccountIDTokenAuth(strict: Optional[bool] = False):
    cls = deepcopy(_ServiceAccountIDTokenAuth)
    cls.strict = strict
    return cls


ServiceAccountIDTokenAuthStrictWhenLive = ServiceAccountIDTokenAuth(
    strict=not settings.TESTING if settings.TESTING else not settings.DEBUG
)


class IsServiceAccount(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user:
            return False
        group = settings.SERVICE_ACCOUNT_GROUP_NAME
        return bool(
            request.user and group in request.user.groups.values_list(
                "name", flat=True
            )
        )


__all__ = [
    "ServiceAccountIDTokenAuth",
    "ServiceAccountIDTokenAuthStrictWhenLive",
    "IsServiceAccount"
]
