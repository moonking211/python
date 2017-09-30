# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from rest_framework import status

from restapi.models.AccountManager import AccountManager
from restapi.testspecs.CreateTestClient import CreateTestClient
from restapi.views.account_manager.AccountManagerDetail import AccountManagerDetail


class AccountManagerDetailSpecs(TestCase, CreateTestClient):
    def setUp(self):
        self.client = Client()
        self.ac_manager_detail = AccountManagerDetail

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.ac_manager_detail, 'queryset'))

    def test__account_manager_detail__not_provided_without_login(self):
        # arrange
        manager = AccountManager.objects.create(status=True, first_name='test')

        # act
        response = self.client.get('/account_managers/{0}'.format(manager.account_manager_id))

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__account_manager_detail__provided_with_login(self):
        # arrange
        self._create_client()
        manager = AccountManager.objects.create(status=True, first_name='test')
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/account_managers/{0}'.format(manager.account_manager_id), follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['status'], True)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_200_OK)
        self.assertEqual(result['first_name'], 'test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
