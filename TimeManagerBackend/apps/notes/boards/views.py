from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotesBoard
from . import serializers
from TimeManagerBackend.lib.viewsets import PatchUpdateModelViewSet
from TimeManagerBackend.apps.users.models.serializers import UserSerializer


# /boards/
# /boards/:id/
class NotesBoardViewSet(PatchUpdateModelViewSet):
    def get_queryset(self):
        """ Only allow users to 'see' boards they are a part of. """
        if getattr(self, 'swagger_fake_view', False):
            return NotesBoard.objects.none()

        return NotesBoard.objects.filter(
            members__in=[self.request.user]
        ).prefetch_related("owner")

    def get_serializer_class(self):
        """
        Select different serializers for:

        - LIST
        - CREATE
        - DETAIL
        """
        if self.action == "list":
            return serializers.NotesBoardListSerializer
        elif self.action == "create":
            return serializers.NotesBoardCreateSerializer

        return serializers.NotesBoardDetailSerializer

    def check_object_permissions(self, request, obj):
        """ Only allow owners to UPDATE or DESTROY a board. """
        if self.action in ("update", "partial_update", "destroy"):
            if self.request.user != obj.owner:
                self.permission_denied(
                    request,
                    message=(
                        "Only the board owner may perform this action."
                    )
                )


# /boards/:id/members/
class BoardMembersView(APIView):
    def get_referred_obj(self, req, pk):
        board = get_object_or_404(NotesBoard, id=pk)

        if board.owner != self.request.user:
            self.permission_denied(
                req,
                message=(
                    "Only the board owner may perform this action."
                )
            )

        return board

    def put(self, request: Request, boards_pk):
        board = self.get_referred_obj(request, boards_pk)
        member_union = set(
            NotesBoard.objects.filter(pk=board.pk).values_list(
                "members__id", flat=True
            )
        )
        new_members = request.data.get("members")
        member_union.union(new_members)
        board.members.set(list(member_union))
        board.save()
        serializer = UserSerializer(
            board.members, many=True, context={"request": self.request}
        )
        return Response(
            {"members": serializer.data},
            status=status.HTTP_200_OK
        )

    def delete(self, request: Request, boards_pk):
        board = self.get_referred_obj(request, boards_pk)
        member_union = set(
            NotesBoard.objects.filter(pk=board.pk).values_list(
                "members__id", flat=True
            )
        )
        member_union.discard(request.data.get("user"))
        board.members = list(member_union)
        board.save()
        return member_union
