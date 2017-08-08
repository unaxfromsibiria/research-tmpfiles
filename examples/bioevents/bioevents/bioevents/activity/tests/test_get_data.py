
from uuid import uuid4

from django.core.urlresolvers import reverse as url_reverse

from django.test.client import Client
from django.utils.timezone import now

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from bioevents.activity.models import SleepEventModel
from bioevents.activity.models import MovementEventModel


class SleepEventSearchTest(APITransactionTestCase):
    """Just simple case.
    """

    def setUp(self):
        now_date = now()
        SleepEventModel(
            time_start=now_date - timedelta(seconds=1800),
            time_end=now_date + timedelta(seconds=3600),
            uid=uuid4()
        ).save()

    def test_get_list_with_once_record(self):
        now_date = now()
        cl = Client()
        resp = cl.get(
            url_reverse("activity:sleep-events-list"),
            {
                "time_start": (now_date - timedelta(seconds=3600)).isoformat(),
                "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
            })

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_get_list_without_records(self):
        now_date = now()
        cl = Client()
        resp = cl.get(
            url_reverse("activity:sleep-events-list"),
            {
                "time_start": (now_date - timedelta(seconds=300)).isoformat(),
                "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
            })

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)


class MovementEventSearchTest(APITransactionTestCase):
    """Check filter by records with correct id.
    """

    correct_id_list = incorrect_id_list = now_date = None
    parts_size = 100

    def setUp(self):
        self.now_date = now_date = now()
        self.correct_id_list = []
        self.incorrect_id_list = []

        for i in range(self.parts_size):
            record = MovementEventModel(
                step_count=i,
                time_start=now_date - timedelta(seconds=1800),
                time_end=now_date + timedelta(seconds=3600),
                uid=uuid4())
            record.save()
            self.correct_id_list.append(record.pk)

        for i in range(self.parts_size):
            record = MovementEventModel(
                step_count=i,
                time_start=now_date + timedelta(seconds=3600),
                time_end=now_date + timedelta(seconds=3601),
                uid=uuid4())
            record.save()
            self.incorrect_id_list.append(record.pk)

    def test_get_list_with_correct_id(self):
        now_date = self.now_date
        cl = Client()
        resp = cl.get(
            url_reverse("activity:move-events-list"),
            {
                "time_start": (now_date - timedelta(seconds=3600)).isoformat(),
                "time_end": (now_date + timedelta(seconds=1800)).isoformat(),
            })

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), self.parts_size)

        for record in data:
            real_id = record.get("id")
            self.assertIn(real_id, self.correct_id_list)
            self.assertNotIn(real_id, self.incorrect_id_list)
