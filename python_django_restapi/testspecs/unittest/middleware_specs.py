# encoding: utf-8

from __future__ import unicode_literals

from mock import Mock

from unittest import TestCase

from rest_framework import status

from restapi.middleware import DisableCSRF, JsonHttpStatusCode, PreAuthentication, Authentication
from restapi.registry import REGISTRY

test_request = Mock()
test_response = Mock()


class Middleware(TestCase):
    def setUp(self):
        self.disable_csrf = DisableCSRF()
        self.json_http_status_code = JsonHttpStatusCode()
        self.pre_authentication = PreAuthentication
        self.authentication = Authentication()

    def test__disable_csrf_class_methods__exists(self):
        self.assert_(hasattr(self.disable_csrf, 'process_request'))

    def test__json_http_status_code_class_methods__exists(self):
        self.assert_(hasattr(self.json_http_status_code, 'process_response'))

    def test__pre_authentication_class_methods__exists(self):
        self.assert_(hasattr(self.pre_authentication, 'process_request'))

    def test__authentication_class_methods__exists(self):
        self.assert_(hasattr(self.authentication, 'process_request'))

    def test__disable_csrf_process_request__return_correct_request(self):
        # arrange
        self.test_request = test_request()
        setattr(self.test_request, '_dont_enforce_csrf_checks', False)

        # act
        self.disable_csrf.process_request(self.test_request)

        # assert
        self.assert_(getattr(self.test_request, '_dont_enforce_csrf_checks'))

    def test__json_http_status_code_process_response__return_correct_response(self):
        # arrange
        def get(value, default=None):
            if value == 'Content-Type':
                return 'application/json'
            return default

        self.test_request = test_request

        self.test_response = test_response
        self.test_response.content = '{"HTTP-STATUS": 500}'
        self.test_response.status_code = 400

        self.test_json_response = test_response()
        self.test_json_response.get = get
        self.test_json_response.content = '{"HTTP-STATUS": 300}'
        self.test_json_response.status_code = 100

        # act
        self.json_http_status_code.process_response(self.test_request, self.test_response)
        self.json_http_status_code.process_response(self.test_request, self.test_json_response)

        # assert
        self.assertEquals(self.test_response.content, '{"HTTP-STATUS": 500}')
        self.assertEquals(self.test_response.status_code, 400)

        self.assertEquals(self.test_json_response.content, '{"HTTP-STATUS": 100}')
        self.assertEquals(self.test_json_response.status_code, status.HTTP_100_CONTINUE)

    def test__authentication_process_request__return_correct_request(self):
        # arrange
        def is_authenticated():
            return False

        self.test_request = test_request()
        self.test_request.META = {'HTTP_X_FORWARDED_FOR': 'Dummy'}
        self.test_request.user.is_authenticated = is_authenticated

        # act
        self.authentication.process_request(self.test_request)

        # assert
        self.assert_(REGISTRY['user'])
