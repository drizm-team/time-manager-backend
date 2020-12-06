from rest_framework import routers
from . import views
from .apps import CoreConfig as CurrentApp
from django.urls import path

app_name = CurrentApp.name
router = routers.SimpleRouter()

urlpatterns = [
    path("", views.TokenObtainPairView.as_view(), name='obtain_delete'),
    path("refresh/", views.TokenRefreshView.as_view(), name='refresh'),
    path("verify/", views.TokenVerifyView.as_view(), name='verify'),
]
urlpatterns += router.urls
