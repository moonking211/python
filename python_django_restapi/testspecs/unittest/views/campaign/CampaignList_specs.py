# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from rest_framework import status

from restapi.views.campaign.CampaignList import CampaignList
from restapi.testspecs.CreateTestData import CreateTestData


class CampaignListSpecs(TestCase, CreateTestData):
    def setUp(self):
        self.client = Client()
        self.campaign_list = CampaignList

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.campaign_list, 'queryset'))
        self.assert_(hasattr(self.campaign_list, 'get_queryset'))

    def test__campaign_list__not_provided_without_login(self):
        # arrange
        self._create_client()
        self.create_campaign(campaign_name='test campaign')

        # act
        response = self.client.get('/campaigns')

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__campaign_list__provided_with_login(self):
        # arrange
        self._create_client()
        self.create_campaign(campaign_name='test campaign')
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/campaigns', follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
