from drizm_django_commons.serializers import HrefModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Event
from TimeManagerBackend.lib.fields import HexColorField


class EventsSerializer(HrefModelSerializer):
    allDay = serializers.BooleanField(
        default=False,
        required=False,
        source="all_day"
    )
    primary_color = HexColorField(required=True)
    secondary_color = HexColorField(required=True)

    class Meta:
        model = Event
        exclude = ["creator", "all_day"]
        extra_kwargs = {
            "self": {
                "view_name": "events:event-detail"
            },
        }

    def to_internal_value(self, data):
        serialized = super().to_internal_value(data)
        request = self.context.get("request")
        serialized["creator"] = request.user
        return serialized

    def validate(self, attrs):
        start = attrs.get("start")
        end = attrs.get("end")

        if start >= end:
            raise ValidationError("End-Date must be after Start-Date.")

        return attrs


class EventsListQueryParamsSerializer(serializers.Serializer):  # noqa abstract
    year = serializers.IntegerField(
        required=True,
        min_value=1000,
        max_value=10000
    )
    month = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=12
    )
