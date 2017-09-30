# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test.client import MULTIPART_CONTENT
from django.test import TestCase
from django.forms.models import model_to_dict

from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from restapi.models.Advertiser import Advertiser
from restapi.testspecs.CreateTestData import CreateTestData


class AdvertiserTest(TestCase, CreateTestData):
    model = Advertiser
    url = '/advertisers'
    url_update = None
    field_to_update = 'advertiser'
    advertiser = None

    def setUp(self):
        self._create_client()
        self._create_object()

    def _create_object(self):
        self.advertiser = self.create_advertiser(advertiser_name='advertiser 1')
        self.url_update = "%s/%s" % (self.url, self.advertiser.pk)

    def test__delete__return_nothing(self):
        # object must exist
        self.model.objects.get(pk=self.advertiser.pk)

        # delete object
        response = self.logged_in_client.delete(self.url_update)
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        # object must not exist
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.advertiser.pk)

    def test__update__return_object(self):
        self.assertEqual(self.model.objects.count(), 1)

        data = model_to_dict(self.model.objects.get(pk=self.advertiser.pk))
        data[self.field_to_update] = "%s updated" % data[self.field_to_update]

        # update
        # pylint: disable=protected-access
        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)
        response = self.logged_in_client.put(self.url_update, encoded, MULTIPART_CONTENT)
        self.assertEqual(response.status_code, HTTP_200_OK)

        obj = self.model.objects.get(pk=self.advertiser.pk)
        self.assertEqual(getattr(obj, self.field_to_update), data[self.field_to_update])
        return obj

    def test__validation_exception__agency_field_is_required(self):
        field_name = 'agency_id'
        self.assertEqual(self.model.objects.count(), 1)

        url = "%s/%s" % (self.url, self.advertiser.pk)
        data = model_to_dict(self.advertiser)
        del data[field_name]

        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)
        response = self.logged_in_client.put(url, encoded, MULTIPART_CONTENT)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(content.get('HTTP-STATUS', None), HTTP_400_BAD_REQUEST)
        self.assertEqual(content.get(field_name, None), u'agency_id field is required.')
