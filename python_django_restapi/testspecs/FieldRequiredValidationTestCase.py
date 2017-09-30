# encoding: utf-8

from __future__ import unicode_literals

import json

from django.test.client import MULTIPART_CONTENT
from django.forms.models import model_to_dict

from rest_framework.status import HTTP_400_BAD_REQUEST


class FieldRequiredValidationTestCase(object):
    def _field_is_required_validation_test(self, field_name, url, obj):
        self.assertEqual(self.model.objects.count(), 1)

        data = model_to_dict(obj)
        del data[field_name]

        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)
        response = self.logged_in_client.put(url, encoded, MULTIPART_CONTENT)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(content.get('HTTP-STATUS', None), HTTP_400_BAD_REQUEST)
        self.assertEqual(content.get(field_name, None), [u'This field is required.'])
