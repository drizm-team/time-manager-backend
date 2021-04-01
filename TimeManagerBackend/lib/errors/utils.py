import re
from typing import Union

from rest_framework.response import Response


def self_test(error_response: Response) -> None:
    """
    Checks the structure of exceptions,
    to ensure that certain formatting rules
    are always respected.
    """
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

    # Matches all special characters except _ and .
    pattern = re.compile(r"(?=\W)(?=[^_.'])")

    for v in ("detail", "code"):
        value = content.get(v)
        if (t := type(value)) != str:
            raise TypeError(
                f"'{v}' type must be 'string', got '{t}'."
            )

        # Make sure that the exceptions have proper formatting
        if r := re.match(pattern, value):
            raise ValueError(
                f"'{v}' cannot contain any special characters, "
                f"except for '.', ' and '_'. Detected forbidden character "
                f"'{r[0]}' in '{value}'."
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
