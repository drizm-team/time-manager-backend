from django.contrib import admin
from drizm_django_commons.admin import SortableAdminMenuMixin


class SiteAdmin(SortableAdminMenuMixin, admin.AdminSite):
    site_header = "TimeManagerBackend Administration"
    index_title = "TimeManagerBackend Administration"
    site_title = "Administration"

    admin_app_ordering = {
        "auth": ("users", "auth"),
    }
