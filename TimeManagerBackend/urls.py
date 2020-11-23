from django.conf import settings
from django.urls import path, include, re_path
from django.views.generic.base import RedirectView

from .apps.users.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    token_destroy_view
)
from .docs.openapi import schema_view

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    # Included URL paths
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    re_path(r'^redoc/$',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    re_path(r'^favicon\.ico$', favicon_view),

    path('tokens/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('tokens/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('tokens/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('tokens/destroy/', token_destroy_view, name='token_destroy'),

    # User defined URL paths
    path(
        'users/',
        include(
            'TimeManagerBackend.apps.users.urls',
            namespace='users'
        )
    ),
    path(
        'notes/',
        include(
            'TimeManagerBackend.apps.notes.urls',
            namespace='notes'
        )
    )
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
