from django.urls import path
from rest_framework.routers import SimpleRouter

from .apps import CoreConfig as CurrentApp
from .boards.views import NotesBoardViewSet, BoardMembersView

app_name = CurrentApp.name

router = SimpleRouter()
router.register(r"boards", NotesBoardViewSet, "boards")

urlpatterns = [
    path(
        "boards/<boards_pk>/members/",
        BoardMembersView.as_view(),
        name="boards-members"
    )
]

urlpatterns += router.urls
