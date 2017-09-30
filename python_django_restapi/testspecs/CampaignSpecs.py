# encoding: utf-8

from __future__ import unicode_literals

import json
from pytz import timezone
from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.forms.models import model_to_dict
from django.test.client import MULTIPART_CONTENT

from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from restapi.models.Campaign import Campaign
from restapi.models.Source import Source
from restapi.models.choices import STATUS_ENABLED
from restapi.models.choices import STATUS_PAUSED
from restapi.testspecs.CreateTestData import CreateTestData

TZ = timezone(settings.TIME_ZONE)


class CampaignTest(TestCase, CreateTestData):
    url = '/campaigns'
    campaign = None
    advertiser = None
    model = Campaign
    data = None

    def setUp(self):
        self._create_client()
        self._create_object()

    def _create_object(self):
        self.advertiser = self.create_advertiser()
        self.tracking_provider = self.create_tracking_provider()
        self.obj = Campaign(advertiser_id=self.advertiser,
                            campaign='campaign 1',
                            attribution_window=0,
                            genre=1,
                            destination_url='http://google.com',
                            domain='google.com',
                            targeting="{}",
                            inflator_text="",
                            frequency_map={"0x0": "3/86400", "320x50": "1/7200", "728x90": "1/7200", "*": "1/28800"},
                            redirect_url='https://google.com',
                            priority=0,
                            daily_spend=1,
                            daily_budget_type='',
                            daily_budget_value=1,
                            flight_budget_type='install',
                            flight_budget_value=1,
                            flight_start_date=datetime.now(),
                            flight_end_date=datetime.now(),
                            distribution_app_sha1_mac=1,
                            distribution_app_sha1_udid=0,
                            distribution_app_sha1_android_id=1,
                            distribution_app_ifa=0,
                            distribution_app_md5_ifa=1,
                            distribution_app_xid=0,
                            distribution_web=1,
                            sampling_rate='0',
                            throttling_rate='0',
                            tracking_provider_id=self.tracking_provider,
                            categories=["IAB1", "IAB1-1", "IAB1-2", "IAB99-1", "IAB99-2", "IAB99-3"])

        Source(source='Facebook').save()
        Source(source='Appbank').save()

        self.obj.save()
        self.campaign = self.obj
        self.data = {'advertiser_id': self.campaign.advertiser_id_id,
                     'campaign': 'new campaign',
                     'iab_classification': 'IAB1 IAB1-1 IAB1-2 IAB99-1',
                     'destination_url': 'http://gootle.com/',
                     'domain': 'apple.com',
                     'genre': 1,
                     'distribution_app_ifa': 'true',
                     'redirect_url': 'https://google.com',
                     'manage_classification': 'IAB99-1 IAB99-2 IAB99-3',
                     'other_iab_classification': 'NEX1-101 NEX2-101]',
                     'flight_start_date': '2014-12-24T14:00:00Z',
                     'flight_end_date': '2014-12-31T23:00:00Z',
                     'daily_budget_value': 0,
                     'flight_budget_value': 0,
                     'total_cost_cap': 0,
                     'total_loss_cap': 0,
                     'daily_cost_cap': 0,
                     'daily_loss_cap': 0
                     }

    def model_to_dict(self, obj):
        data = model_to_dict(obj)
        if 'frequency_map' in data:
            data['frequency_map'] = json.dumps(data['frequency_map'])
        if 'categories' in data:
            data['iab_classification'] = data['categories']
        for key, value in data.items():
            if isinstance(value, datetime):
                date = data[key]
                if date:
                    if not date.tzinfo:
                        date = TZ.localize(date)
                    data[key] = date.strftime("%Y-%m-%dT%H:%M:%SZ")
        return data

    def test__invalid_create_without_distribution__return_exception(self):
        data = self.model_to_dict(self.campaign)
        data.update({'distribution_app_sha1_mac': False,
                     'distribution_app_sha1_udid': False,
                     'distribution_app_sha1_android_id': False,
                     'distribution_app_ifa': False,
                     'distribution_app_md5_ifa': False,
                     'distribution_app_xid': False,
                     'distribution_web': False})
        data['iab_classification'] = ["IAB1", "IAB1-1", "IAB1-2"]
        del data['paused_at']

        encoded = json.dumps(data)
        response = self.logged_in_client.put("%s/%s" % (self.url, self.campaign.pk),
                                             encoded,
                                             content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, '{"HTTP-STATUS": 400, "distributions": "No distributions"}')

    def test__asterisk_last_in_db__return_nothing(self):
        data = self.model_to_dict(self.campaign)
        data['frequency_map'] = '{"*": "1/28800", "0x0": "3/86400", "320x50": "1/7200", "728x90": "1/7200"}'
        data['inflator_text'] = 'Facebook 3\nAppbank 2\n* 1'
        data['iab_classification'] = ["IAB1", "IAB1-1", "IAB1-2"]
        del data['paused_at']
        encoded = json.dumps(data)

        # pylint: disable=unused-variable
        response = self.logged_in_client.put("%s/%s" % (self.url, self.campaign.pk),
                                             encoded,
                                             content_type="application/json")
        self.assertEqual(response.status_code, HTTP_200_OK)

        # pylint: disable=line-too-long
        obj = Campaign.objects.get(advertiser_id=self.advertiser)
        inflator_text = obj.inflator_text
        self.assertEqual(inflator_text, "Facebook 3\r\nAppbank 2\r\n* 1")

    def test__create__return_object(self):
        model = self.model

        # 2-nd object must not exist
        self.assertRaises(model.DoesNotExist, model.objects.get, pk=self.campaign.pk + 1)

        # create 2-nd object
        response = self.logged_in_client.post(self.url, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2-nd object must exist
        obj = model.objects.get(pk=self.campaign.pk + 1)
        return obj

    def test__categories__return_nothing(self):
        data = self.model_to_dict(self.campaign)
        data['iab_classification'] = ["IAB1", "IAB1-1", "IAB1-2"]
        data['manage_classification'] = ["IAB99-1", "IAB99-2", "IAB99-3"]
        data['other_iab_classification'] = ["NEX1-101", "NEX2-101"]

        # pylint: disable=protected-access
        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)

        # pylint: disable=unused-variable
        response = self.logged_in_client.put("%s/%s" % (self.url, self.campaign.pk), encoded, MULTIPART_CONTENT)
        self.assertEqual(response.status_code, HTTP_200_OK)
        obj = Campaign.objects.get(advertiser_id=self.advertiser)
        self.assertEqual(obj.categories, 'IAB1 IAB1-1 IAB1-2 IAB99-1 IAB99-2 IAB99-3 NEX1-101 NEX2-101')

    def test__invalid_priority__return_exception(self):
        data = self.model_to_dict(self.campaign)
        data.update({'priority': 101})
        del data['paused_at']

        encoded = json.dumps(data)
        response = self.logged_in_client.put("%s/%s" % (self.url, self.campaign.pk),
                                             encoded,
                                             content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        result = json.loads(response.content)
        self.assertEqual(result['HTTP-STATUS'], HTTP_400_BAD_REQUEST)
        self.assertEqual(result['priority'], 'Priority can not be less than 0 and more than 100')

    def test__invalid_destination_url_min_length__return_exception(self):
        data = self.model_to_dict(self.campaign)
        data.update({'destination_url': 'ya.ru'})

        encoded = json.dumps(data)
        response = self.logged_in_client.put("%s/%s" % (self.url, self.campaign.pk),
                                             encoded,
                                             content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        result = json.loads(response.content)
        self.assertEqual(result['HTTP-STATUS'], HTTP_400_BAD_REQUEST)
        self.assertEqual(result['destination_url'], 'Must be at least 10 characters long')

    def _test__paused_at__return_nothing(self):
        self.obj.status = STATUS_ENABLED
        self.obj.save()
        self.assertEqual(self.campaign.status, STATUS_ENABLED)
        self.assertEqual(self.campaign.paused_at, None)
        self.obj.status = STATUS_PAUSED
        self.obj.save()
        self.assertEqual(self.campaign.status, STATUS_PAUSED)
        self.assertNotEqual(self.campaign.paused_at, None)
