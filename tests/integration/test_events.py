from datetime import datetime, timedelta
from typing import Optional

from django.http import QueryDict
from django.utils import timezone
from drizm_commons.utils import all_keys_present
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..conftest import create_test_user, TEST_USER_PASSWORD

BASE_TIME = datetime.now()
EXAMPLE_CONTENT = {
            "title": "Some title",
            "primary_color": "#ffffff",
            "secondary_color": "#ababab",
            "start": BASE_TIME.isoformat(),
            "end": (BASE_TIME + timedelta(hours=5)).isoformat()
        }


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
        example_content = content or EXAMPLE_CONTENT
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

    # noinspection PyMethodMayBeStatic
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
            AND the end-date is after the start-date
        THEN I should be able to create a new event
        """
        url = reverse(self.list)

        # Try without being logged in, this should fail
        res = self.client.post(url, EXAMPLE_CONTENT)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        # Create a new note while logged in, this should work
        self.client.force_authenticate(user=self.user)
        res = self.client.post(url, EXAMPLE_CONTENT)
        assert res.status_code == status.HTTP_201_CREATED
        content = res.json()
        self._test_response_body(content)

        # Make sure the aliasing of all_day to allDay works as expected
        # The below should work and show up in the database,
        # under it's actual name of 'all_day' instead of the provided 'allDay'
        req_content = {**EXAMPLE_CONTENT, "allDay": True}
        res = self.client.post(url, req_content)
        assert res.status_code == status.HTTP_201_CREATED
        content = res.json()
        assert content.get("allDay") is True

        # Attempt to create a new event,
        # with the 'start_time', being the same as the 'end_time'.
        # This should fail.
        current_time = datetime.now()
        req_content = {
            **EXAMPLE_CONTENT,
            "start": current_time.isoformat(),
            "end": current_time.isoformat()
        }
        res = self.client.post(url, req_content)
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

        # Create a test event.
        # We use only UTC-Times for this because this is consistent
        # with Frontend, which sends only UTC-Times when creating Notes
        # and instead provides the timezone for filtering only,
        # while converting the times client-side.
        start_time = timezone.datetime(
            year=2020,
            month=12,
            day=31,
            hour=22,
            minute=12,
            second=0
        )
        end_time = timezone.datetime(
            year=2020,
            month=12,
            day=31,
            hour=23,
            minute=0,
            second=0
        )
        self._sample_create(
            {
                "title": "Some title 15",
                "primary_color": "#ffffff",
                "secondary_color": "#ababab",
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        )

        # Try without being logged in, this should fail
        res = self.client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        # Try without the required query params of 'month' and 'year'
        # This should fail.
        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # Try filtering for the month we created in.
        # This should work and return the event.
        self.client.force_authenticate(user=self.user)
        # This is for the month of December (so 12) but -1
        # And for German-Time, which is 1 hour ahead of UTC.
        url = self._generate_filter_url(
            year=2020,
            month=11,
            tz=60
        )
        res = self.client.get(url)
        assert len(res.json()) == 1

        # Now we check for the first month of the next year,
        # This should still work because the 'end_date' of the event,
        # is at 11pm UTC, which, since we filter based on German time offset,
        # would be 00:00 of the 1st of Jan. 2021.
        # As such this should still give us the event back.
        url = self._generate_filter_url(
            year=2021,
            month=0,
            tz=60
        )
        res = self.client.get(url)
        assert len(res.json()) == 1
