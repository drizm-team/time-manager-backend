from rest_framework import viewsets
from rest_framework.request import Request
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status

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
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        query_serializer = serializers.EventsListQueryParamsSerializer(
            data={"month": month, "year": year}
        )
        query_serializer.is_valid(raise_exception=True)

        queryset = self.get_queryset()
        events = queryset.filter(
            Q(start__month__lte=month) &
            Q(end__month__gte=month) &
            Q(start__year__lte=year) &
            Q(end__year__gte=year)
        ).all()
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
