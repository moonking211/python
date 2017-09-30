# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from rest_framework import status

from restapi.views.user.UserList import UserList
from restapi.testspecs.CreateTestClient import CreateTestClient


class UserListViewsSpecs(TestCase, CreateTestClient):
    def setUp(self):
        self.client = Client()
        self.user_detail = UserList

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.user_detail, 'post'))
        self.assert_(hasattr(self.user_detail, 'queryset'))
        self.assert_(hasattr(self.user_detail, 'get_queryset'))

    def test__user_list__not_provided_without_login(self):
        # act
        response = self.client.get('/auth_users')

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_403_FORBIDDEN)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__user_list__provided_with_login(self):
        # arrange
        self._create_client()
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/auth_users', follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['HTTP-STATUS'], status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
