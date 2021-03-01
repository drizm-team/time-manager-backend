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

    def get_members(self):
        serializer = serializers.NotesBoardMembersSerializer(
            data=self.request.data, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data.get("members")

    def get_response(self, board):
        serializer = UserSerializer(
            board.members, many=True, context={"request": self.request}
        )
        return Response(
            {"members": serializer.data},
            status=status.HTTP_200_OK
        )

    def put(self, request: Request, boards_pk):
        board = self.get_referred_obj(request, boards_pk)
        members = self.get_members()

        for member in members:
            board.members.add(member)
        board.save()
        return self.get_response(board)

    def delete(self, request: Request, boards_pk):
        board = self.get_referred_obj(request, boards_pk)
        members = self.get_members()

        if board.owner in members:
            self.permission_denied(
                request, message="The board owner cannot be removed."
            )

        for member in members:
            board.members.remove(member)
        board.save()
        return self.get_response(board)
