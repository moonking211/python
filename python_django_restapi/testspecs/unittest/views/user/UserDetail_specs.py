# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from rest_framework import status

from restapi.models import User
from restapi.testspecs.CreateTestClient import CreateTestClient
from restapi.views.user.UserDetail import UserDetail


class UserDetailViewsSpecs(TestCase, CreateTestClient):
    def setUp(self):
        self.client = Client()
        self.user_detail = UserDetail

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.user_detail, 'put'))
        self.assert_(hasattr(self.user_detail, 'patch'))
        self.assert_(hasattr(self.user_detail, 'queryset'))

    def test__user_list__not_provided_without_login(self):
        # arrange
        self._create_client()
        user = User.objects.get(username='user@mng.com')

        # act
        response = self.client.get('/auth_users/{0}'.format(user.user_id))

        # assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.content,
                         '{"HTTP-STATUS": 403, "detail": "Authentication credentials were not provided."}')

    def test__user_list__provided_with_login(self):
        # arrange
        self._create_client()
        user = User.objects.get(username='user@mng.com')
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/auth_users/{0}'.format(user.user_id), follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['HTTP-STATUS'], 200)
        self.assertEqual(result['username'], user.username)
        self.assertEqual(result['user_id'], user.user_id)
        self.assertEqual(result['email'], user.email)
