from django.contrib.auth import get_user_model
from typing import Optional


def create_test_user(email: Optional[str] = None,
                     password: Optional[str] = None) -> tuple:
    User = get_user_model()
    email = email or "tester@tester.de"
    password = password or "topTierthingy42"
    user = User.objects.create_user(
        email=email,
        password=password
    )
    return user, email, password
