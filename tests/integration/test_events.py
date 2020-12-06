from datetime import datetime, timedelta
from typing import Optional

from django.http import QueryDict
from django.utils import timezone
from drizm_commons.utils import all_keys_present
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..conftest import create_test_user, TEST_USER_PASSWORD


class TestEvents(APITestCase):
    def setUp(self) -> None:
        self.user_pw = TEST_USER_PASSWORD
        self.user = create_test_user()

        app_base = "events:event-%s"
        self.list = app_base % "list"
        self.detail = app_base % "detail"

    def _sample_create(self, content=None):
        """ Generate a generic test event """
        url = reverse(self.list)

        current_time = datetime.now()
        example_content = content or {
            "title": "Some title",
            "primary_color": "#ffffff",
            "secondary_color": "#ababab",
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(hours=5)).isoformat()
        }
        self.client.force_authenticate(user=self.user)
        res = self.client.post(url, example_content)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(user=None)

        return res.json()

    def _generate_filter_url(self,
                             year: int,
                             month: int,
                             tz: Optional[int] = None) -> str:
        """ Generate a URL for the list endpoint, that includes query params """
        query_params = QueryDict("", mutable=True)
        query_params["year"] = year
        query_params["month"] = month
        query_params["tz"] = tz or 0

        return "{base_url}?{query_params}".format(
            base_url=reverse(self.list),
            query_params=query_params.urlencode(),
        )

    def _test_response_body(self, body: dict):
        assert all_keys_present(
            body,
            (
                "title", "primary_color", "secondary_color",
                "start", "end", "allDay", "self"
            )
        )
        # Make sure these two attributes really do not get output
        assert not all_keys_present(body, ("creator", "id"))

    def test010_create(self):
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to create a new event
        THEN I should be able to create a new event
        """
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

        # Create a new note while logged in, this should work
        self.client.force_authenticate(user=self.user)
        res = self.client.post(url, example_content)
        assert res.status_code == status.HTTP_201_CREATED
        content = res.json()
        self._test_response_body(content)

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
        """
        GIVEN I have a user account
            AND I am logged in
        WHEN I ask to list all events in a range
            AND I provide query params to specify the desired range
        THEN I should be able to see all events that were created by me
            AND that match the specified range including the timezone I specified
        """
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
        url = self._generate_filter_url(
            year=datetime.now().year,
            month=datetime.now().month - 1
        )
        res = self.client.get(url)
        assert res.status_code == status.HTTP_200_OK
        content = res.json()
        assert type(content) == list
        assert len(content) == 1

        # We create last months data here,
        # so this should not show our event from this month
        url = self._generate_filter_url(
            year=datetime.now().year,
            month=datetime.now().month - 2
        )
        res = self.client.get(url)
        assert res.status_code == status.HTTP_200_OK
        content = res.json()
        assert type(content) == list
        assert len(content) == 0

    def test030_list_filtering(self):
        # All the below times are in UTC
        # Now we have an event from 22:14 - 23:14
        # on the last day of November
        start_time = timezone.datetime(
            year=2020, month=11, day=30,
            hour=22, minute=14, second=27
        )
        end_time = start_time + timezone.timedelta(minutes=60)

        self._sample_create(
            {
                "title": "Some title",
                "primary_color": "#ffffff",
                "secondary_color": "#ababab",
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        )

        # German-Time (+1 UTC)
        # Lets say we are in Germany now and want to filter our calendar
        # We expect this to be in Nov, as well as Dec because
        # of the timezone change
        url = self._generate_filter_url(
            year=start_time.year,
            month=start_time.month - 1,
            tz=(-60)
        )

        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        assert len(res.json()) == 1

        url = self._generate_filter_url(
            year=start_time.year,
            month=start_time.month,
            tz=(-60)
        )
        res = self.client.get(url)
        assert len(res.json()) == 1

        url = self._generate_filter_url(
            year=start_time.year,
            month=start_time.month - 2,
            tz=(-60)
        )
        res = self.client.get(url)
        assert len(res.json()) == 0

    def test040_list_filtering_2(self):
        start_time = timezone.datetime(
            year=2020, month=11, day=30,
            hour=22, minute=14, second=27
        )

        # Test everything above but without an end attribute
        self._sample_create(
            {
                "title": "Some title",
                "primary_color": "#ffffff",
                "secondary_color": "#ababab",
                "start": start_time.isoformat(),
            }
        )
        # German-Time (+1 UTC)
        # Lets say we are in Germany now and want to filter our calendar
        # We expect this to be in Nov, as well as Dec because
        # of the timezone change
        url = self._generate_filter_url(
            year=start_time.year,
            month=start_time.month - 1,
            tz=(-60)
        )

        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        assert len(res.json()) == 1

        url = self._generate_filter_url(
            year=start_time.year,
            month=start_time.month,
            tz=(-60)
        )
        res = self.client.get(url)
        assert len(res.json()) == 0

        url = self._generate_filter_url(
            year=start_time.year,
            month=start_time.month - 2,
            tz=(-60)
        )
        res = self.client.get(url)
        assert len(res.json()) == 0
