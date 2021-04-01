from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from TimeManagerBackend.lib.commons.firestore import get_firestore
from TimeManagerBackend.lib.commons.mixins import SerializerContextMixin
from . import serializers
from ..boards.models import NotesBoard
from ..groups.models import NotesGroup


# /boards/:id/notes/:id/
class BoardNotesView(SerializerContextMixin, APIView):
    serializer_class = serializers.BoardNotesSerializer

    def put(self, request, boards_pk, pk):
        _ = get_object_or_404(
            NotesBoard.objects.filter(members__in=[request.user]),
            id=boards_pk
        )
        data = {"parent": boards_pk, "id": pk, **request.data}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    # noinspection PyMethodMayBeStatic
    def delete(self, request, boards_pk, pk):
        board = get_object_or_404(
            NotesBoard.objects.filter(members__in=[request.user]),
            id=boards_pk
        )

        db = get_firestore()
        col_ref = db.collection("notes__boards", str(board.pk), "notes")
        doc_ref = col_ref.document(pk)

        if not doc_ref.get().exists:
            raise Http404

        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# /boards/:id/groups/:id/notes/:id/
class GroupNotesView(SerializerContextMixin, APIView):
    serializer_class = serializers.GroupNotesSerializer

    def put(self, request, boards_pk, groups_pk, pk):
        group = get_object_or_404(
            NotesGroup.objects.filter(parent__members__in=[request.user]),
            id=groups_pk, parent_id=boards_pk
        )

        data = {"parent": group.pk, "id": pk, **request.data}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def delete(self, request, boards_pk, groups_pk, pk):
        group = get_object_or_404(
            NotesGroup.objects.filter(parent__members__in=[request.user]),
            id=groups_pk, parent_id=boards_pk
        )

        db = get_firestore()
        col_ref = db.collection("notes__groups", str(group.pk), "notes")
        doc_ref = col_ref.document(pk)

        if not doc_ref.get().exists:
            raise Http404

        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
