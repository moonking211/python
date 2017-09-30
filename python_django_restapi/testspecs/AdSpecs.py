# encoding: utf-8

from __future__ import unicode_literals

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from django.test.client import MULTIPART_CONTENT
from django.forms.models import model_to_dict
from django.test import TestCase
import json

from restapi.models.Ad import Ad
from restapi.models.choices import STATUS_ENABLED, AD_TYPE_RICHMEDIA, AD_TYPE_CHOICES, AD_SIZE_CHOICES
from restapi.testspecs.CreateTestData import CreateTestData


class AdTest(TestCase, CreateTestData):
    model = Ad
    url = '/ads'
    url_update = None
    field_to_update = 'ad'

    ad_entry = None
    campaign = None
    ad_group = None
    data = None

    def setUp(self):
        self._create_client()
        self._create_object()

    def _create_object(self):
        self.ad_entry = self.create_ad()
        self.ad_entry.save()
        self.url_update = "%s/%s" % (self.url, self.ad_entry.pk)

        self.data = {"ad": "new_ad",
                     "ad_group_id": self.ad_entry.ad_group_id.pk,
                     "ad_type": AD_TYPE_CHOICES[1][0],
                     "attrs": "",
                     "bid": 0,
                     "external_args": "",
                     "html": '<a href="{CLICK_URL}"><img src="https://mng-monarch.s3.amazonaws.com/1124/no_endcard_320x480.jpg" width="300" height="250"></a>',
                     "inflator_text": "* 1.00",
                     "preview_html": "<a href='{CLICK_URL}'><img src='https://mng-monarch.s3.amazonaws.com/1124/no_endcard_320x480.jpg' width='320' height='480'></a>",
                     "redirect_url": "https://test.com",
                     "size": AD_SIZE_CHOICES[5][0],
                     "status": STATUS_ENABLED,
                     "tag": ""}

    def test__create__return_object(self):
        # 2-nd object must not exist
        self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.ad_entry.pk + 1)

        # create 2-nd object
        response = self.logged_in_client.post(self.url, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        # 2-nd object must exist
        obj = self.model.objects.get(pk=self.ad_entry.pk + 1)
        return obj

    def test__list__return_list_of_two(self):
        # list with 1 object
        response = self.logged_in_client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        result = json.loads(response.content)['results']

        # pylint: disable=unidiomatic-type check
        self.assertTrue(type(result) == list)
        self.assertEqual(len(result), 1)

        # list with 2 objects
        response = self.logged_in_client.post(self.url, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        response = self.logged_in_client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        result = json.loads(response.content)['results']
        self.assertEqual(len(result), 2)

        return result

    def test__update__agency(self):
        self.assertEqual(self.model.objects.count(), 1)

        data = model_to_dict(self.ad_entry)
        data[self.field_to_update] = "%s updated" % data[self.field_to_update]

        # update
        encoded = self.logged_in_client._encode_data(data, MULTIPART_CONTENT)
        response = self.logged_in_client.put(self.url_update, encoded, MULTIPART_CONTENT)
        self.assertEqual(response.status_code, HTTP_200_OK)

        obj = self.model.objects.get(pk=self.ad_entry.pk)
        self.assertEqual(getattr(obj, self.field_to_update), data[self.field_to_update])

    # TODO(victor): uncomment this once I figure out what to do with ad pruning table.
    # def test__delete__return_nothing(self):
    #     # object must exist
    #     self.model.objects.get(pk=self.ad_entry.pk)
    #
    #     # delete object
    #     response = self.logged_in_client.delete(self.url_update)
    #     self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
    #
    #     # object must not exist
    #     self.assertRaises(self.model.DoesNotExist, self.model.objects.get, pk=self.ad_entry.pk)

    def test__ad_type__validation_exception(self):
        self.data['ad_type'] = 'A'

        response = self.logged_in_client.put(self.url_update, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        self.assertEqual(response.content, '{"HTTP-STATUS": 400, "ad_type": ["A valid integer is required."]}')

    def test__richmedia_type__validation_exception(self):
        self.data['ad_type'] = AD_TYPE_RICHMEDIA

        response = self.logged_in_client.put(self.url_update, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.content,
            '{"HTTP-STATUS": 400, "i_url": "For MRAID or RICHMEDIA types i_url field should not be empty"}')

    def test__i_url__validation_exception(self):
        incorrect_url = "incorrect_url"
        self.data['ad_type'] = AD_TYPE_RICHMEDIA
        self.data['i_url'] = incorrect_url

        response = self.logged_in_client.put(self.url_update, json.dumps(self.data), content_type="application/json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.content, ('{"HTTP-STATUS": 400, "i_url": "Incorrect i_url field format: %s"}' % incorrect_url))
