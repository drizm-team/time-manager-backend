from django.urls import path

from .apps import CoreConfig as CurrentApp
from .views import notes_viewset_detail, notes_viewset_list

app_name = CurrentApp.name

urlpatterns = [
    path("", notes_viewset_list, name="note-list"),
    path("<str:pk>/", notes_viewset_detail, name="note-detail")
]
