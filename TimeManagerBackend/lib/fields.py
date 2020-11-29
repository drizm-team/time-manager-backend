import re

from rest_framework import serializers


class HexColorField(serializers.Field):
    """ Saves hex color-values of lengths 3 or 6 to int in the Database """
    default_error_messages = {
        "incorrect_format": "Incorrect hex color format."
    }

    def to_representation(self, value: int):
        # Simply convert our value back to a string and add a #
        return hex(value).replace("0x", "#")

    def to_internal_value(self, data):
        # Validate that it is either a 3 or 6 digit hex-code with a # in it
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', data):
            self.fail("incorrect_format")

        # strip the #
        data = data[1:]

        # Expand 3-digit hex for consistency
        if len(data) == 3:
            data = "".join(c * 2 for c in data)

        # Save the integer representation in the database
        # we do this because it is less bytes than saving it as a string
        return int(data, 16)
