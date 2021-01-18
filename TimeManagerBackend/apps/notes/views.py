from django.http import Http404
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .models import Note
from .models.serializers import (
    NotesSerializer,
    NotesResponseSchema,
    NotesRequestSchema
)


@method_decorator(
    name="list", decorator=swagger_auto_schema(
        operation_summary="List all created Notes",
        responses={
            status.HTTP_200_OK: NotesResponseSchema(many=True)
        }
    )
)
@method_decorator(
    name="retrieve", decorator=swagger_auto_schema(
        operation_summary="Retrieve singular Note",
        responses={
            status.HTTP_200_OK: NotesResponseSchema()
        }
    )
)
@method_decorator(
    name="destroy", decorator=swagger_auto_schema(
        operation_summary="Delete Note"
    )
)
class NotesViewSet(mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = NotesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Note.objects.none()

        return Note.objects.filter(creator=self.request.user)

    @swagger_auto_schema(
        operation_summary="Overwrite Note",
        operation_description="Overwrite a note object, "
                              "does not check whether the object "
                              "exists or not, so can be used "
                              "for both create and update.",
        responses={
            status.HTTP_200_OK: NotesResponseSchema(),
            status.HTTP_400_BAD_REQUEST: "Validation failed",
            status.HTTP_403_FORBIDDEN: "Note already exists but this user "
                                       "does not have permissions to edit it"
        },
        request_body=NotesRequestSchema
    )
    def update(self, request, *args, **kwargs):
        # Build the dataset required to construct the note
        pk = kwargs.get("pk")
        data = request.data
        data["id"] = pk

        # Attempt to obtain the object but not from a subset
        # This is to handle the case where a user overwrites
        # an object created by another user that would not get
        # handled by this view by default because the queryset is scoped
        note = Note.objects.filter(pk=pk)
        if note:
            if note[0].creator != request.user:
                raise PermissionDenied
        try:
            o = self.get_object()
            serializer = self.get_serializer(o, data=data, partial=False)
        except Http404:
            serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
            headers=headers
        )

    # noinspection PyMethodMayBeStatic
    def get_success_headers(self, data):
        try:
            return {'Location': str(
                data[api_settings.URL_FIELD_NAME]
            )}
        except (TypeError, KeyError):
            return {}


notes_viewset_list = NotesViewSet.as_view({
    "get": "list"
})
notes_viewset_detail = NotesViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "delete": "destroy"
})
