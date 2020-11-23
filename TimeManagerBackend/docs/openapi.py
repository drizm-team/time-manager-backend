from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .. import __version__


schema_view = get_schema_view(
   openapi.Info(
      title="TimeManagerBackend API",
      default_version=__version__,
      description="",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

__all__ = ["schema_view"]
