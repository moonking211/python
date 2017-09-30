# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from rest_framework import status

from restapi.testspecs.CreateTestData import CreateTestData
from restapi.views.trading_desk.TradingDeskList import TradingDeskList


class TradingDeskListSpecs(TestCase, CreateTestData):
    def setUp(self):
        self.client = Client()
        self.trading_desk_list = TradingDeskList

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.trading_desk_list, 'queryset'))

    def test__trading_desk_list__not_provided_without_login(self):
        # arrange
        self._create_client()

        # act
        response = self.client.get('/trading_desks')

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__trading_desk_list__provided_with_login(self):
        # arrange
        self._create_client()
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/trading_desks', follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
