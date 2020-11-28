from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import migrations


def create_grafana_user(*args):
    User = get_user_model()
    User.objects.create_superuser(
        email=settings.PROM_USER,
        password=settings.PROM_PASSWORD
    )


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_gcp_accounts'),
    ]

    operations = [
        migrations.RunPython(create_grafana_user),
    ]
