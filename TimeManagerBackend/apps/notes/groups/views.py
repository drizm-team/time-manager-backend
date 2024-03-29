from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from TimeManagerBackend.lib.commons.firestore import get_firestore
from TimeManagerBackend.lib.viewsets import PatchUpdateModelViewSet
from . import serializers
from .models import NotesGroup


# /boards/:id/groups/
# /boards/:id/groups/:id/
class NotesGroupViewSet(PatchUpdateModelViewSet):
    def get_queryset(self):
        """
        Only allow users to 'see' groups that are
        a part of a board that the user is a part of.
        """
        if getattr(self, 'swagger_fake_view', False):
            return NotesGroup.objects.none()

        return NotesGroup.objects.prefetch_related(
            "parent"
        ).filter(parent__members__in=[self.request.user])

    def get_serializer_class(self):
        """ Select a different serializer for LIST and DETAIL. """
        if self.action in ("list",):
            return serializers.NotesGroupListSerializer

        return serializers.NotesGroupDetailSerializer

    def get_object(self):
        """ Returns the object the view is displaying. """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {
            "parent_id": self.kwargs["boards_pk"],
            self.lookup_field: self.kwargs[lookup_url_kwarg]
        }
        obj = get_object_or_404(self.get_queryset(), **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def create(self, request, boards_pk):
        data = {"parent": boards_pk, **request.data}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def destroy(self, request: Request, *args, **kwargs):
        serializer = serializers.NotesGroupDeleteSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)

        instance: NotesGroup = self.get_object()
        notes = instance.notes
        if serializer.data.get("cascade"):
            for n in notes:
                n.reference.delete()
        else:
            db = get_firestore()
            col_ref = db.collection(
                "notes__boards", str(instance.parent_id), "notes"
            )
            for n in notes:
                pk = n.pk
                data = n._snapshot  # noqa private
                col_ref.document(pk).set(data.to_dict())
                n.reference.delete()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
