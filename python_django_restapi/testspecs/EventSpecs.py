# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test.client import MULTIPART_CONTENT
from django.forms.models import model_to_dict
from django.test import TestCase

from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from restapi.models.Event import Event
from restapi.testspecs.CreateTestData import CreateTestData


class EventTest(TestCase, CreateTestData):
    model = Event
    url = '/events'
    url_update = None
    field_to_update = 'event'
    campaign = None
    event = None
    data = None

    def setUp(self):
        self._create_client()
        self._create_object()

    def _create_object(self):
        self.campaign = self.create_campaign()
        self.event = self.create_event(campaign_id=self.campaign)
        self.url_update = "%s/%s" % (self.url, self.event.pk)
        self.data = json.dumps({"campaign_id": self.campaign.campaign_id, "event": "new event"})

    def test__create__return_object(self):
        # 2-nd object must not exist
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.event.pk + 1)

        # create 2-nd object
        response = self.logged_in_client.post(self.url, self.data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2-nd object must exist
        obj = self.model.objects.get(pk=self.event.pk + 1)
        return obj

    def test__list__return_list_of_two(self):
        # list with 1 object
        response = self.logged_in_client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        result = json.loads(response.content)['results']

        # pylint: disable=unidiomatic-type check
        self.assertTrue(type(result) == list)
        self.assertEqual(len(result), 1)

        # list with 2 objects
        response = self.logged_in_client.post(self.url, self.data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.logged_in_client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        result = json.loads(response.content)['results']
        self.assertEqual(len(result), 2)
        return result

    def test__update__return_object(self):
        self.assertEqual(self.model.objects.count(), 1)

        data = model_to_dict(self.model.objects.get(pk=self.event.pk))
        data[self.field_to_update] = "%s updated" % data[self.field_to_update]

        # update
        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)
        response = self.logged_in_client.put(self.url_update, encoded, MULTIPART_CONTENT)
        self.assertEqual(response.status_code, HTTP_200_OK)

        obj = self.model.objects.get(pk=self.event.pk)
        self.assertEqual(getattr(obj, self.field_to_update), data[self.field_to_update])
        return obj

    def test__delete__return_nothing(self):
        # object must exist
        self.assertEqual(self.model.objects.count(), 1)

        # delete object
        response = self.logged_in_client.delete(self.url_update)
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        # object must not exist
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.event.pk)
