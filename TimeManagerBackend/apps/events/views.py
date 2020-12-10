from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Event
from .models import serializers


class EventsViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.EventsSerializer

    def get_queryset(self):
        return Event.objects.filter(
            creator=self.request.user
        )

    @swagger_auto_schema(
        operation_summary="List all available Events",
        query_serializer=serializers.EventsListQueryParamsSerializer()
    )
    def list(self, request: Request, *args, **kwargs):
        # Extract and validate the query args
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        tz = request.query_params.get("tz")
        query_serializer = serializers.EventsListQueryParamsSerializer(
            data={"month": month, "year": year, "tz": tz}
        )
        query_serializer.is_valid(raise_exception=True)

        # Month counts up from 0 so we have to add 1 to it
        month = query_serializer.validated_data.get("month") + 1
        year = query_serializer.validated_data.get("year")
        tz = query_serializer.validated_data.get("tz")

        start_date = timezone.datetime(
            day=1, month=month, year=year
        )
        end_date = start_date + relativedelta(months=1)

        # If the timezone of the user was e.g. 60 mins ahead of UTC
        # which is the servers time, then we would get sent '60'.
        # Since we get the dates in UTC themselves we need to actually
        # subtract that number for proper querying
        start_date -= relativedelta(minutes=tz)
        end_date -= relativedelta(minutes=tz)

        queryset = self.get_queryset()
        events = queryset.filter(
            Q(
                end__isnull=True,
                start__range=(start_date, end_date)
            ) | Q(
                Q(start__range=(start_date, end_date)) |
                Q(end__range=(start_date, end_date))
            )
        ).all()
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
