from django.conf import settings
from django_prometheus.exports import ExportToDjangoView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes
)
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsPrometheusAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user:
            return False
        return bool(
            request.user and request.user.email == settings.PROM_USER
        )


@swagger_auto_schema(method="post", auto_schema=None)  # noqa type
@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsPrometheusAdmin])
def prom_view(request: Request, *args, **kwargs):
    """ Protected variant of the default Prometheus metrics view """
    django_wsgi_request = request._request  # noqa protected
    res = ExportToDjangoView(django_wsgi_request)
    return res
