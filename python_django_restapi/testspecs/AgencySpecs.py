# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test.client import MULTIPART_CONTENT
from django.forms.models import model_to_dict
from django.test import TestCase

from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from restapi.models.choices import STATUS_ENABLED, CURRENCY_USD
from restapi.models.TradingDesk import MANAGE_TRADING_DESK_ID
from restapi.models.Agency import Agency

from restapi.testspecs.FieldRequiredValidationTestCase import FieldRequiredValidationTestCase
from restapi.testspecs.CreateTestData import CreateTestData


class AgencySpecs(TestCase, CreateTestData, FieldRequiredValidationTestCase):
    model = Agency
    url = '/agencies'
    url_update = None
    field_to_update = 'agency'
    agency = None
    data = None

    def setUp(self):
        self._create_client()
        self._create_object()

    def _create_object(self):
        self.agency = self.create_agency()
        self.url_update = "%s/%s" % (self.url, self.agency.pk)
        self.data = {'trading_desk_id': self.agency.trading_desk_id_id,
                     'agency': 'new agency',
                     'status': STATUS_ENABLED,
                     'currency': CURRENCY_USD,
                     'contact': 'contact info',
                     'account_manager': MANAGE_TRADING_DESK_ID}

    def test__create__agency(self):
        # 2-nd object must not exist
        self.assertEqual(self.model.objects.count(), 1)
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.agency.pk + 1)

        # create 2-nd object
        response = self.logged_in_client.post(self.url, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2-nd object must exist
        self.assertEqual(self.model.objects.count(), 2)
        self.assertIsNotNone(self.model.objects.get(pk=self.agency.pk + 1))

    def test__update__agency(self):
        self.assertEqual(self.model.objects.count(), 1)

        data = model_to_dict(self.agency)
        data[self.field_to_update] = "%s updated" % data[self.field_to_update]

        # update
        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)
        response = self.logged_in_client.put(self.url_update, encoded, MULTIPART_CONTENT)

        self.assertEqual(response.status_code, HTTP_200_OK)

        obj = self.model.objects.get(pk=self.agency.pk)
        self.assertEqual(getattr(obj, self.field_to_update), data[self.field_to_update])

    def test__delete__agency(self):
        self.assertEqual(self.model.objects.count(), 1)

        # delete object
        response = self.logged_in_client.delete(self.url_update)
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        # object must not exist
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.agency.pk)

    def test__validation_exception__status_field_is_required(self):
        self._field_is_required_validation_test('status', self.url_update, self.agency)

    def test__validation_exception__currency_field_is_required(self):
        self._field_is_required_validation_test('currency', self.url_update, self.agency)

    def test__validation_exception__contact_field_is_required(self):
        self._field_is_required_validation_test('contact', self.url_update, self.agency)
