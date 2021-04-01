import json
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import migrations
from drizm_commons.utils.pathing import Path


def create_service_account_group(*args) -> None:
    group, _ = Group.objects.get_or_create(
        name=settings.SERVICE_ACCOUNT_GROUP_NAME
    )


def create_service_accounts(*args) -> None:
    User = get_user_model()
    for fp in [
        Path(path) for path in settings.GCP_CREDENTIALS.iterdir()
    ]:
        with open(fp, "r") as fin:
            content = json.load(fin)
        user = User.objects.create_user(
            sub=content.get("client_id"),
            email=content.get("client_email"),
            password="".join(
                secrets.choice(
                    string.ascii_letters
                ) for _ in range(64)
            )
        )
        group, _ = Group.objects.get_or_create(
            name=settings.SERVICE_ACCOUNT_GROUP_NAME
        )
        user.groups.set([group])


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_service_account_group),
        migrations.RunPython(create_service_accounts),
    ]
