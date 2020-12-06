import re
from typing import Union

from rest_framework.response import Response


def camel_to_snake(name: str):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def self_test(error_response: Response) -> None:
    """ Makes sure that the generated error response is valid """
    content = error_response.data
    detail: Union[str, list] = content.get("detail")
    code: str = content.get("code")

    keys_actual = set(content.keys())
    keys_expect = {"detail", "code"}

    if not keys_expect.issubset(keys_actual):
        raise ValueError(
            "Error-Response structure invalid. "
            f"Expected keys '{keys_expect}', got '{keys_actual}'."
        )

    for v in ("detail", "code"):
        value = content.get(v)
        if (t := type(value)) != str:
            raise TypeError(
                f"'{v}' type must be 'string', got '{t}'."
            )

    if not detail.endswith("."):
        raise ValueError(
            "Expected '.' at the end of detail message. "
            f"Full message is: '{detail}'."
        )

    if any(l.isupper() for l in code):
        raise ValueError(
            f"'code' needs to be all lowercase, got '{code}'."
        )
