# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from restapi.testspecs.CreateTestData import CreateTestData
from restapi.views.audit_log.AuditLogList import AuditLogList


class AuditLogListSpecs(TestCase, CreateTestData):
    def setUp(self):
        self.client = Client()
        self.audit_log_list = AuditLogList

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.audit_log_list, 'queryset'))

    def test__augit_log_list__not_provided_without_login(self):
        # arrange
        self._create_client()

        # act
        response = self.client.get('/audit_logs')

        # assert
        result = json.loads(response.content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result['HTTP-STATUS'], 403)
        self.assertEqual(result['detail'], 'Authentication credentials were not provided.')

    def test__audit_log_list__provided_with_login(self):
        # arrange
        self._create_client()
        self.client.login(username='user@mng.com', password='password1')

        # act
        response = self.client.get('/audit_logs', follow=True)

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['HTTP-STATUS'], 200)
        self.assertEqual(response.status_code, 200)
