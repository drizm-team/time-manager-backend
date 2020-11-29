from rest_framework import routers

from . import views
from .apps import CoreConfig as CurrentApp

app_name = CurrentApp.name

router = routers.SimpleRouter()

router.register(r"", views.EventsViewSet, basename="event")

urlpatterns = []

urlpatterns += router.urls
