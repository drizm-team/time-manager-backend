from datetime import datetime, timedelta

from django.http import QueryDict
from drizm_commons.utils import all_keys_present
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..conftest import create_test_user


class TestEvents(APITestCase):
    def setUp(self) -> None:
        self.user, self.email, self.password = create_test_user()

        self.base = "events:event-%s"
        self.list = self.base % "list"
        self.detail = self.base % "detail"

    def _sample_create(self):
        url = reverse(self.list)
        current_time = datetime.now()
        example_content = {
            "title": "Some title",
            "primary_color": "#ffffff",
            "secondary_color": "#ababab",
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(hours=5)).isoformat()
        }
        self.client.force_authenticate(user=self.user)
        self.client.post(url, example_content)
        self.client.force_authenticate(user=None)

    def _generate_filter_url(self, query_params):
        return "{base_url}?{query_params}".format(
            base_url=reverse(self.list),
            query_params=query_params.urlencode(),
        )

    def test010_create(self):
        url = reverse(self.list)
        current_time = datetime.now()
        example_content = {
            "title": "Some title",
            "primary_color": "#ffffff",
            "secondary_color": "#ababab",
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(days=2)).isoformat()
        }

        # Make sure it does not work without auth
        res = self.client.post(url, example_content)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        # Make sure it works under normal conditions
        self.client.force_authenticate(user=self.user)
        res = self.client.post(url, example_content)
        assert res.status_code == status.HTTP_201_CREATED
        content = res.json()
        assert all_keys_present(
            content,
            (
                "title", "primary_color", "secondary_color",
                "start", "end", "allDay", "self"
            )
        )
        assert not all_keys_present(content, ("creator", "id"))

        # Does our aliasing of all_day to allDay work on write as well?
        example_content["allDay"] = True
        res = self.client.post(url, example_content)
        assert res.status_code == status.HTTP_201_CREATED
        content = res.json()
        assert content.get("allDay") is True

        # Test with wrong datasets
        # end-date == start-date
        example_content["end"] = current_time
        res = self.client.post(url, example_content)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test020_list(self):
        url = reverse(self.list)
        # Create a test event
        self._sample_create()

        # Make sure it does not work without auth
        res = self.client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        # Make sure it does not work without query args
        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # We expect to get something back here,
        # because we created it in the current month
        query_params = QueryDict("", mutable=True)
        query_params["year"] = datetime.now().year
        query_params["month"] = datetime.now().month
        url = self._generate_filter_url(query_params)
        res = self.client.get(url)
        assert res.status_code == status.HTTP_200_OK
        content = res.json()
        assert type(content) == list
        assert len(content) == 1

        # We create last months data here,
        # so this should not show our event from this month
        query_params["month"] = datetime.now().month - 1
        url = self._generate_filter_url(query_params)
        res = self.client.get(url)
        assert res.status_code == status.HTTP_200_OK
        content = res.json()
        assert type(content) == list
        assert len(content) == 0
