import logging
from typing import Dict, Any

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from drizm_commons.utils.various import camel_to_snake
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .utils import self_test


def get_server_error_response(exc):
    if not settings.DEBUG and not settings.TESTING:
        # Automatically log all critical server errors
        logger = logging.getLogger("failure-500")
        logger.error(exc)

    return Response(
        {
            "detail": "An Unknown Error occured.",
            "code": "unknown_error"
        },
        status=500
    )


def get_detail(exc: APIException) -> str:
    try:
        detail = exc.detail
    except AttributeError:
        try:
            detail = exc.__class__.default_detail
        except AttributeError:
            # This is a last resort handling for Django exceptions
            # That do not have these attributes
            detail = exc.args[0]

    # Frontend needs unified handling of detail so we can only send strings
    # This means that if we encounter multiple messages,
    # we only send the first one (this could happen with e.g. ValidationError)
    if type(detail) in (list, tuple):
        detail = detail[0]
    if type(detail) == dict or issubclass(type(detail), dict):
        detail = list(detail.values())[0]

        # Some error messages may be nested one level deeper
        # unpack those as well
        if type(detail) == list:
            detail = detail[0]

    # Per convention detail must always end with a '.'
    detail = str(detail)
    if not detail.endswith("."):
        detail += "."

    return detail


def get_code(exc: APIException) -> str:
    try:
        code = exc.get_codes()
    except AttributeError:
        try:
            code = exc.__class__.default_code
        except AttributeError:
            # Django's exceptions do not have a code attribute at all
            # So we just convert the class name to a lowercase snake_case string
            code = camel_to_snake(exc.__class__.__name__)

    if type(code) == dict or issubclass(type(code), dict):
        code = list(code.values())[0]

        # Some error codes may be nested one level deeper
        # unpack those as well
        if type(code) == list:
            code = code[0]

    return str(code)


def get_status(exc: APIException) -> int:
    try:
        status = exc.status_code
    except AttributeError:
        params = (exc.__class__, "status_code")
        if hasattr(*params):
            status = getattr(*params)
        else:
            # Last ditch effort fallback
            return 500  # BAD_REQUEST

    return int(status)


def global_default_exception_handler(
        exc: APIException,
        context: Dict[str, Any]
) -> Response:
    """
    Serializes all exceptions to the following default structure:
    {
        "detail": "A message.",
        "code": "error_not_valid"
    }
    """
    if settings.DEBUG_PROPAGATE_EXCEPTIONS:
        return exception_handler(exc, context)

    # Manually map Django exceptions here
    # and transform them to DRF exceptions for consistency
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    try:
        status = get_status(exc)

        # In case a catastrophic failure occurs,
        # we cannot risk leaking any info
        if status == 500 and (
                not settings.TESTING and not settings.DEBUG
        ):  # SERVER_ERROR
            return get_server_error_response(exc)

        resp = Response(
            {
                "detail": get_detail(exc),
                "code": get_code(exc)
            },
            status=status
        )
    except Exception as exc:  # noqa E722
        # Silence the errors in production but raise them in development
        if not settings.TESTING and not settings.DEBUG:
            resp = exception_handler(exc, context)

            # Again, in case a 500 occurs we should send basically
            # no data to external sources because it may be sensitive
            if resp.status_code == 500:  # SERVER_ERROR
                return get_server_error_response(exc)

        else:
            raise exc
    else:  # if no error occurred
        if settings.TESTING:
            self_test(resp)

    return resp
