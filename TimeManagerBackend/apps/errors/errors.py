from rest_framework.exceptions import APIException


class ValidationError(APIException):
    default_code = "validation_error"
    default_detail = "Validation failed for provided request"
    status_code = 422

    def __init__(self, *args, **kwargs) -> None:
        super(ValidationError, self).__init__(*args)
        self.serializer_errors = kwargs.get("serializer_errors")


class EmailInUse(APIException):
    default_code = "not_unique"
    default_detail = "Email %s already in use"
    status_code = 400

    def __init__(self, *args, **kwargs) -> None:
        super(EmailInUse, self).__init__(*args)
        self.email = kwargs.get("email")


class NotFoundException(APIException):
    default_code = "not_found"
    default_detail = "Element not found"
    status_code = 404


__all__ = ["ValidationError", "EmailInUse", "NotFoundException"]
