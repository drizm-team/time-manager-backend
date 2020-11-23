from django.contrib.admin.apps import AdminConfig


class CustomAdmin(AdminConfig):
    default_site = "TimeManagerBackend.admin.SiteAdmin"
