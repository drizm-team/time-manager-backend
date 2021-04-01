from drizm_django_commons.serializers import HrefModelSerializer, HexColorField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Event


class EventsSerializer(HrefModelSerializer):
    allDay = serializers.BooleanField(
        default=False,
        required=False,
        source="all_day"
    )
    primary_color = HexColorField(required=True)
    secondary_color = HexColorField(required=True)

    class Meta:
        self_view = "events:event-detail"
        model = Event
        exclude = ["creator", "all_day"]

    def to_internal_value(self, data):
        serialized = super().to_internal_value(data)
        request = self.context.get("request")
        serialized["creator"] = request.user
        return serialized

    def validate(self, attrs):
        start = attrs.get("start")
        end = attrs.get("end")

        if not end:
            return attrs

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
        min_value=0,
        max_value=11
    )
    tz = serializers.IntegerField(
        min_value=-(int(12.5 * 60)),
        max_value=int(14 * 60),
        default=0,
        required=False,
        allow_null=True
    )
