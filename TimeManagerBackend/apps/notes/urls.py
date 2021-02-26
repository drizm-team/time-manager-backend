from rest_framework.routers import SimpleRouter

from .apps import CoreConfig as CurrentApp
from .views import NotesBoardViewSet

app_name = CurrentApp.name

router = SimpleRouter()
router.register(r"boards", NotesBoardViewSet, "boards")

urlpatterns = []
urlpatterns += router.urls
