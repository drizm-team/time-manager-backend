import os

import requests
import urllib3
from django.utils.deconstruct import deconstructible
from google.cloud.storage import Client
from google.cloud.storage.blob import _quote  # noqa private
from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import clean_name


@deconstructible
class EmulatedGCS(GoogleCloudStorage):  # noqa must implement abstract
    @property
    def client(self):
        if self._client is None:
            os.environ["STORAGE_EMULATOR_HOST"] = self.custom_endpoint
            session = requests.Session()
            session.verify = False
            urllib3.disable_warnings(
                urllib3.exceptions.InsecureRequestWarning
            )
            self._client = Client(
                _http=session,
                project=self.project_id,
                credentials=self.credentials,
                client_options={
                    "api_endpoint": self.custom_endpoint
                }
            )

        return self._client

    def url(self, name):
        name = self._normalize_name(clean_name(name))
        blob = self.bucket.blob(name)
        no_signed_url = (
            self.default_acl == 'publicRead' or not self.querystring_auth
        )

        if not self.custom_endpoint and no_signed_url:
            return blob.public_url
        elif no_signed_url:
            return (
                '{storage_base_url}/download/storage/'
                'v1/b/test/o/{quoted_name}'.format(
                    storage_base_url=self.custom_endpoint,
                    quoted_name=_quote(name, safe=b"/~"),
                )
            )
        elif not self.custom_endpoint:
            return blob.generate_signed_url(self.expiration)
        else:
            return blob.generate_signed_url(
                expiration=self.expiration,
                api_access_endpoint=self.custom_endpoint,
            )
