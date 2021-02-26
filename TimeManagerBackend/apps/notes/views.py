from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import NotesBoard, NotesGroup
from .models.serializers import boards, groups, notes
from ...lib.commons.mixins import SerializerContextMixin
from ...lib.viewsets import PatchUpdateModelViewSet


# /boards/
# /boards/:id/
class NotesBoardViewSet(PatchUpdateModelViewSet):
    def get_queryset(self):
        """ Only allow users to 'see' boards they are a part of. """
        if getattr(self, 'swagger_fake_view', False):
            return NotesBoard.objects.none()

        return NotesBoard.objects.filter(
            Q(owner=self.request.user) |
            Q(members__in=self.request.user)
        ).prefetch_related("owner")

    def get_serializer_class(self):
        """
        Select different serializers for:

        - LIST
        - CREATE
        - DETAIL
        """
        if self.action == "list":
            return boards.NotesBoardListSerializer
        elif self.action == "create":
            return boards.NotesBoardCreateSerializer

        return boards.NotesBoardDetailSerializer

    def check_object_permissions(self, request, obj):
        """ Only allow owners to UPDATE or DESTROY a board. """
        if self.action in ("update", "destroy"):
            if self.request.user != obj.owner:
                self.permission_denied(
                    request,
                    message=(
                        "Only the board owner may perform this action."
                    )
                )


# /boards/:id/members/
class BoardMembersViewSet(APIView):
    def get_referred_obj(self, req, pk):
        board = get_object_or_404(NotesBoard, id=pk)

        if board.owner != self.request.user.pk:
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
        member_union.add(request.data.get("user"))
        board.members = list(member_union)
        board.save()
        return member_union

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


# /boards/:id/notes/:id/
class BoardNotesViewSet(SerializerContextMixin, APIView):
    serializer_class = notes.BoardNotesSerializer

    def put(self, request, board_pk, pk):
        pass

    def delete(self, request, board_pk, pk):
        pass


# /boards/:id/groups/
# /boards/:id/groups/:id/
class NotesGroupViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        """
        Only allow users to 'see' groups that are
        a part of a board that the user is a part of.
        """
        if getattr(self, 'swagger_fake_view', False):
            return NotesGroup.objects.none()

        return NotesGroup.objects.prefetch_related(
            "parent"
        ).filter(
            Q(parent__owner=self.request.user) |
            Q(parent__members__in=self.request.user)
        )

    def get_serializer_class(self):
        """ Select a different serializer for LIST and DETAIL. """
        if self.action in ("list", "create"):
            return groups.NotesGroupListSerializer

        return groups.NotesGroupDetailSerializer

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
            "board_pk": self.kwargs["board_pk"],
            self.lookup_field: self.kwargs[lookup_url_kwarg]
        }
        obj = get_object_or_404(self.get_queryset(), **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


# /boards/:id/groups/:id/notes/:id/
class GroupNotesViewSet(SerializerContextMixin, APIView):
    serializer_class = notes.GroupNotesSerializer

    def put(self, request, board_pk, group_pk, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

    def delete(self, request, board_pk, group_pk, pk):
        pass
