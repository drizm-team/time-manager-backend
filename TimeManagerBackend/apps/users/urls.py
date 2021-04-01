from django.urls import path
from rest_framework import routers

from . import views

app_name = "users"
router = routers.SimpleRouter()

router.register(r"", views.UserViewSet, basename="user")

urlpatterns = [
    path(
        "__flush_expired__/",
        views.__manage_flush_expired__,
        name="flush_expired"
    )
]

urlpatterns += router.urls
