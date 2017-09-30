# encoding: utf-8

from __future__ import unicode_literals

import json

from django.db import connection
from django.test import TestCase

from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from restapi.models.choices import STATUS_PAUSED, STATUS_ENABLED
from restapi.models.AdGroup import AdGroup
from restapi.testspecs.CreateTestData import CreateTestData


class AdGroupTest(TestCase, CreateTestData):
    url = '/ad_groups'
    url_update = None
    ad_group = None
    model = AdGroup
    campaign = None

    def setUp(self):
        self._create_client()
        self._create_object()

    def _create_object(self):
        self.campaign = self.create_campaign()
        self.ad_group = self.create_ad_group(campaign_id=self.campaign)
        self.url_update = "%s/%s" % (self.url, self.ad_group.pk)
        self.data = {'campaign_id': self.ad_group.campaign_id_id,
                     'targeting': '{"country":["USA"], "os":"Android"}',
                     'ad_group': 'new ad_group',
                     'frequency_interval': 1,
                     'max_frequency': 2,
                     'distribution_web': True,
                     'flight_start_date': '2014-12-24T14:00:00Z',
                     'flight_end_date': '2014-12-31T23:00:00Z',
                     'daily_budget_value': 0,
                     'flight_budget_value': 0,
                     'total_cost_cap': 0,
                     'total_loss_cap': 0,
                     'daily_cost_cap': 0,
                     'daily_loss_cap': 0
                     }

    def test__create__return_object(self):
        model = self.model

        # 2-nd object must not exist
        self.assertRaises(model.DoesNotExist, model.objects.get, pk=self.ad_group.pk + 1)

        # create 2-nd object
        response = self.logged_in_client.post(self.url, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2-nd object must exist
        obj = model.objects.get(pk=self.ad_group.pk + 1)
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
        response = self.logged_in_client.post(self.url, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.logged_in_client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        result = json.loads(response.content)['results']
        self.assertEqual(len(result), 2)

        return result

    def test__delete__return_nothing(self):
        # object must exist
        self.model.objects.get(pk=self.ad_group.pk)

        # delete object
        response = self.logged_in_client.delete(self.url_update)
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        # object must not exist
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.ad_group.pk)

    def test__invalid_create_event_args_invalid_json__return_exception(self):
        self.assertEqual(self.model.objects.count(), 1)
        self.data['event_args'] = "{..."

        response = self.logged_in_client.put(self.url_update, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, '{"HTTP-STATUS": 400, "event_args": ["Invalid format"]}')

    def test__asterisk_last_in_db__return_nothing(self):
        self.ad_group.frequency_map = {"*": "1/28800", "0x0": "3/86400", "320x50": "1/7200", "728x90": "1/7200"}
        self.ad_group.save()
        cursor = connection.cursor()
        cursor.execute("SELECT frequency_map AS json_str FROM ad_group WHERE ad_group_id=%s" % self.ad_group.pk)
        row = cursor.fetchone()
        self.assertEqual(row[0].encode(), '{"320x50":"1/7200","0x0":"3/86400","728x90":"1/7200","*":"1/28800"}')

    def test__invalid_priority__return_exception(self):
        self.assertEqual(self.model.objects.count(), 1)
        self.data['priority'] = "101"

        response = self.logged_in_client.put(self.url_update, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        result = json.loads(response.content)
        self.assertEqual(result['HTTP-STATUS'], HTTP_400_BAD_REQUEST)
        self.assertEqual(result['priority'], 'Priority can not be less than 0 and more than 100')

    def test__paused_at__return_nothing(self):
        self.ad_group.status = STATUS_ENABLED
        self.ad_group.save()

        self.assertEqual(self.ad_group.status, STATUS_ENABLED)
        self.assertEqual(self.ad_group.paused_at, None)
        self.ad_group.status = STATUS_PAUSED
        self.ad_group.save()
        self.assertEqual(self.ad_group.status, STATUS_PAUSED)
        self.assertNotEqual(self.ad_group.paused_at, None)
