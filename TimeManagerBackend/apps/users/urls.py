from django.urls import path

from .views import (
    user_viewset_detail,
    user_viewset_list,
    user_viewset_change_password,
    __manage_flush_expired__
)

app_name = "users"

urlpatterns = [
    path("", user_viewset_list, name="user-list"),
    path("<int:pk>/", user_viewset_detail, name="user-detail"),
    path(
        "<int:pk>/change-password/",
        user_viewset_change_password,
        name="user-change-password"
    ),
    path(
        "__flush_expired__/",
        __manage_flush_expired__,
        name="flush_expired"
    )
]
