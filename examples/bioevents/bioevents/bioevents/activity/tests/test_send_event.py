
import json
from uuid import uuid4

from django.core.urlresolvers import reverse as url_reverse

from django.test.client import Client
from django.utils.timezone import now

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITransactionTestCase


class ViewApiCase(APITransactionTestCase):
    """Base test class with helper
    """

    def run_request(self, url_name: str, data: dict, method="post"):
        """Helper for request
        """
        cl = Client()
        return getattr(cl, method, cl.get)(
            url_reverse("activity:{}".format(url_name)),
            json.dumps(data),
            content_type="application/json")


class SleepEventTest(ViewApiCase):
    """Event save test.
    """

    def setUp(self):
        pass

    def test_correct_save(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "time_start": (now_date - timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
        }
        resp = self.run_request("sleep-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_save_with_incorrect_location(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "point": ["12000", "123123"],
            "time_start": (now_date - timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
        }
        resp = self.run_request("sleep-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_correct_save_with_location(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "point": ["10.1111", "10.1"],
            "time_start": (now_date - timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
        }
        resp = self.run_request("sleep-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_incorrect_save_with_wrong_dates(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "point": ["10.1111", "10.1"],
            "time_start": (now_date + timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date - timedelta(seconds=1800)).isoformat(),
        }
        resp = self.run_request("sleep-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class MovementEventTest(ViewApiCase):
    """Event movement save test.
    """

    def setUp(self):
        pass

    def test_correct_save(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "time_start": (now_date - timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
            "step_count": 1,
        }
        resp = self.run_request("move-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_save_with_incorrect_type_steps(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "time_start": (now_date - timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
            "step_count": uuid4().hex,
        }
        resp = self.run_request("move-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_with_incorrect_val_steps(self):
        now_date = now()
        data = {
            "uid": str(uuid4()),
            "time_start": (now_date - timedelta(seconds=1800)).isoformat(),
            "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
            "step_count": -1,
        }
        resp = self.run_request("move-events-list", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
