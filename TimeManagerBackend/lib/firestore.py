from functools import lru_cache

import grpc
from django.conf import settings
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import Client
from google.cloud.firestore_v1.services.firestore import FirestoreClient
from google.cloud.firestore_v1.services.firestore.transports import (
    FirestoreGrpcTransport
)
from google.oauth2 import service_account


@lru_cache
def get_firestore() -> Client:
    credentials = service_account.Credentials.from_service_account_file(
        settings.GS_CREDENTIALS_FILE
    )
    db_settings = settings.FIRESTORE_DATABASES["default"]

    # Production does not define extra settings
    if not db_settings:
        return Client(credentials=credentials)

    channel = grpc.insecure_channel(
        f"{db_settings.get('HOST')}:{db_settings.get('PORT')}"
    )
    transport = FirestoreGrpcTransport(channel=channel)

    initialize_app(credentials)
    client: Client = firestore.client()
    client._firestore_api_internal = FirestoreClient(transport=transport)
    return client


__all__ = ["get_firestore"]
