from rest_framework import routers
from . import views
from .apps import CoreConfig as CurrentApp
app_name = CurrentApp.name
router = routers.SimpleRouter()
urlpatterns = []
urlpatterns += router.urls
