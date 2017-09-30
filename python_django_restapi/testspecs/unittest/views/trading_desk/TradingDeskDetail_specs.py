# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from restapi.testspecs.CreateTestData import CreateTestData
from restapi.views.trading_desk.TradingDeskDetail import TradingDeskDetail


class TradingDeskDetailSpecs(TestCase, CreateTestData):
    def setUp(self):
        self.client = Client()
        self.trading_desk_detail = TradingDeskDetail

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.trading_desk_detail, 'queryset'))

    def test__audit_log_detail__not_provided_without_login(self):
        # arrange
        user = self._create_client()

        # act
        response = self.client.get('/trading_desks/{0}'.format(user.trading_desk_id))

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result['HTTP-STATUS'], 403)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__audit_log_detail__provided_with_login(self):
        # arrange
        user = self._create_client()
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/trading_desks/{0}'.format(user.trading_desk_id), follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['trading_desk_id'], user.trading_desk_id)
        self.assertEqual(result['HTTP-STATUS'], 200)
        self.assertEqual(response.status_code, 200)
