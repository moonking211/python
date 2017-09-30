# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from restapi.views.campaign.CampaignDetail import CampaignDetail
from restapi.testspecs.CreateTestData import CreateTestData


class CampaignDetailSpecs(TestCase, CreateTestData):
    def setUp(self):
        self.client = Client()
        self.campaign_detail = CampaignDetail

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.campaign_detail, 'queryset'))

    def test__campaign_detail__not_provided_without_login(self):
        # arrange
        self._create_client()
        campaign = self.create_campaign(campaign_name='test campaign')

        # act
        response = self.client.get('/campaigns/{0}'.format(campaign.campaign_id))

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result['HTTP-STATUS'], 403)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__campaign_detail__provided_with_login(self):
        # arrange
        self._create_client()
        campaign = self.create_campaign(campaign_name='test campaign')
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/campaigns/{0}'.format(campaign.campaign_id), follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['HTTP-STATUS'], 200)
        self.assertEqual(result['campaign'], 'test campaign')
        self.assertEqual(response.status_code, 200)
