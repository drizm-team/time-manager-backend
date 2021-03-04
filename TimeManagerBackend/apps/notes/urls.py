from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .apps import CoreConfig as CurrentApp
from .boards.views import NotesBoardViewSet, BoardMembersView
from .groups.views import NotesGroupViewSet
from .notes.views import BoardNotesView, GroupNotesView

app_name = CurrentApp.name

router = SimpleRouter()
router.register(r"boards", NotesBoardViewSet, basename="boards")

nested_router = NestedSimpleRouter(
    router, r"boards", lookup="boards"  # translates to kwarg boards_pk
)
nested_router.register(r"groups", NotesGroupViewSet, basename="groups")

urlpatterns = [
    path(
        "boards/<boards_pk>/members/",
        BoardMembersView.as_view(),
        name="boards-members"
    ),
    path(
        "boards/<boards_pk>/notes/<pk>/",
        BoardNotesView.as_view(),
        name="boards-notes"
    ),
    path(
        "boards/<boards_pk>/groups/<groups_pk>/notes/<pk>/",
        GroupNotesView.as_view(),
        name="groups-notes"
    )
]

urlpatterns += router.urls
urlpatterns += nested_router.urls
