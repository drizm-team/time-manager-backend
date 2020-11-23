from rest_framework.exceptions import APIException, ValidationError as ValErr
from rest_framework.response import Response
from rest_framework.views import exception_handler
from typing import Union

from .errors import ValidationError, EmailInUse


def global_default_exception_handler(
        exc: APIException,
        context: dict
) -> Response:
    if type(exc) == ValErr:
        return Response({
            "detail": exc.detail,
            "code": ValidationError.default_code
        }, exc.status_code)
    try:
        exc_details = exc.get_full_details()
    except Exception:  # noqa E402
        return exception_handler(exc, context)

    detail = _get_error_msg(exc_details, exc)
    code = exc_details.get("code")
    resp = Response({
        "detail": detail,
        "code": code
    }, exc.status_code)

    if isinstance(exc, ValidationError):
        resp.data["detail"] = exc.serializer_errors
    elif isinstance(exc, EmailInUse):
        resp.data["detail"] = exc.default_detail % exc.email

    return resp


def _get_error_msg(exc_details: dict, exc: APIException) -> Union[str, list]:
    if not (m := exc_details.get("message")):
        if not (m := exc_details.get("messages")):
            return exc.default_code
    return m
