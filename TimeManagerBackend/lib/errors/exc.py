from rest_framework.exceptions import APIException
from rest_framework import status


class ValidationError(APIException):
    default_code = "validation_error"
    default_detail = "Validation failed for provided request"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, *args, **kwargs) -> None:
        super(ValidationError, self).__init__(*args)
        self.serializer_errors = kwargs.get("serializer_errors")


class EmailInUse(APIException):
    default_code = "not_unique"
    default_detail = "Email %s already in use"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, *args, **kwargs) -> None:
        super(EmailInUse, self).__init__(*args)
        self.email = kwargs.get("email")


class NotFoundException(APIException):
    default_code = "not_found"
    default_detail = "Element not found"
    status_code = status.HTTP_404_NOT_FOUND


class PasswordMismatchException(APIException):
    default_code = "password_mismatch"
    default_detail = "Provided password does not match actual"
    status_code = status.HTTP_400_BAD_REQUEST


class NotAuthenticatedException(APIException):
    default_code = "not_authenticated"
    default_detail = "Authentication credentials were not provided"
    status_code = status.HTTP_401_UNAUTHORIZED


__all__ = [
    "ValidationError", "EmailInUse",
    "NotFoundException", "PasswordMismatchException",
    "NotAuthenticatedException"
]
