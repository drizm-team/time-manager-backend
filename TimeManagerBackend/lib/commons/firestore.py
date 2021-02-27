from functools import lru_cache

from drizm_commons.utils.type import AttrDict

try:
    import grpc
    from django.conf import settings
    from firebase_admin import firestore, initialize_app
    from firebase_admin.credentials import Certificate
    from google.cloud.firestore import Client
    from google.cloud.firestore_v1 import _helpers, DocumentSnapshot  # noqa private
    from google.cloud.firestore_v1.gapic.firestore_client import (
        FirestoreClient
    )
    from google.cloud.firestore_v1.gapic.transports.firestore_grpc_transport import (
        FirestoreGrpcTransport
    )
except ImportError:
    raise TypeError(
        "In order to use the Firestore features of this package, "
        "you need to install the 'google-cloud-firestore' and "
        "'firebase-admin' packages."
    )


@lru_cache
def get_firestore() -> Client:
    credentials = Certificate(
        str(settings.GS_CREDENTIALS_FILE)
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
    client._rpc_metadata_internal = _helpers.metadata_with_prefix(
        client._database_string  # noqa protected
    )

    # Authorize the Emulator, check:
    # https://github.com/firebase/firebase-tools/issues/1363#issuecomment-498364771
    client._rpc_metadata_internal.append(  # noqa protected
        ("authorization", "Bearer owner")
    )
    return client


def DocumentWrapper(snapshot: DocumentSnapshot) -> AttrDict:
    """
    A wrapper around a Firestore DocumentSnapshot,
    to bring a Django-Model-esque API to a Snapshot
    and make it compatible with custom Serializer Fields.
    """
    wrapper = AttrDict()
    wrapper["_snapshot"] = snapshot
    wrapper["reference"] = snapshot.reference
    wrapper["id"] = snapshot.id
    wrapper["pk"] = snapshot.id

    snapshot_data = snapshot.to_dict()
    if not snapshot_data:
        return wrapper

    def _wrap(data: dict, ad: AttrDict) -> AttrDict:
        """ Recursively wrap objects (dicts) as AttrDicts. """
        for k, v in data.items():
            if isinstance(v, dict):
                ad[k] = _wrap(v, AttrDict())
            else:
                ad[k] = v
        return ad

    for key, value in snapshot_data.items():
        if isinstance(value, dict):
            wrapper[key] = _wrap(value, AttrDict())
        else:
            wrapper[key] = value

    return wrapper


__all__ = ["get_firestore", "DocumentWrapper"]
