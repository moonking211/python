from restapi.models.choices import AD_STATUS_DISAPPROVED, AD_STATUS_NEW
from restapi.testspecs.CreateTestData import CreateTestData
from restapi.models.AuditLog import AUDIT_ACTION_UPDATE
from restapi.views.ad.AdsResubmit import AdsResubmit
from restapi.models.AuditLog import AuditLog
from restapi.models.Ad import Ad

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from mng.test import spec
from mock import Mock
import json


class AdsResubmitSpec(spec(AdsResubmit), CreateTestData):
    subject = None
    ad_service = None
    request = None

    ad_group = None
    ad1 = None
    ad2 = None
    ad3 = None

    ad_type = 1
    encrypted_ad_id = 'HcMSVtnbTX6FZS1OcaBwwQ'
    creative_id = 1
    size = '300x250'
    redirect_url = 'http://itunes.apple.com/'
    i_url = 'http://itunes.2apple.com/'

    def before_each(self):
        self._create_client()
        self.ad_group = self.create_ad_group()

        self.ad1 = self.__ad_object_create(self.ad_group, 0, 0, 'ad 1', 0, 'google.com', AD_STATUS_DISAPPROVED)
        self.ad2 = self.__ad_object_create(self.ad_group, 0, 0, 'ad 2', 0, 'google.com', AD_STATUS_DISAPPROVED)
        self.ad3 = self.__ad_object_create(self.ad_group, 0, 0, 'ad 3', 0, 'google.com', AD_STATUS_DISAPPROVED)

        ad_service = Mock()
        request = Mock()
        request.QUERY_PARAMS = {}

        self.request = request
        self.ad_service = ad_service
        self.subject = AdsResubmit(ad_service=lambda: ad_service)

    def test__post__ad_resubmit_all(self):
        ad_query_set = Ad.objects.all()
        self.assertEqual(3, ad_query_set.count())
        self.assertTrue(self.__is_adx_status(ad_query_set, AD_STATUS_DISAPPROVED))
        ad_ids_list = [self.ad1.pk, self.ad2.pk, self.ad3.pk]

        self.request.DATA = {'src_ad_ids': ad_ids_list}
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertTrue(self.__is_adx_status(Ad.objects.all(), AD_STATUS_NEW))
        self.assertTrue(response.data is not None and response.data)

        audit_log_qs = AuditLog.objects.filter(item_id__in=ad_ids_list, audit_action=AUDIT_ACTION_UPDATE)
        self.assertEqual(3, audit_log_qs.count())
        for audit_log_entry in audit_log_qs:
            self.assertEqual(audit_log_entry.old_data, '{"adx_status": "disapproved"}')
            self.assertEqual(audit_log_entry.new_data, '{"adx_status": "new"}')

    def test__post__ad_resubmit_bad_request_arguments(self):
        self.request.DATA = {'src_ad_ids': ['bad_request_long_list_expected']}
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data is None)

    def test__post__ad_resubmit_no_ads_were_found(self):
        # send wrong ad_id
        self.request.DATA = {'src_ad_ids': [self.ad3.pk+1]}
        response = self.subject.post(self.request)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data == AdsResubmit.no_ads_found_msg)

    # pylint: disable=no-self-use
    def __is_adx_status(self, ad_query_set, adx_status):
        is_adx_status = True
        for ad_entry in ad_query_set:
            if ad_entry.adx_status != adx_status:
                is_adx_status = False

        return is_adx_status

    # pylint: disable=no-self-use
    def __ad_object_create(self, ad_group, creative_id, ad_type, ad_name, bid, i_url, adx_status):
        ad_object = Ad(ad_group_id=ad_group,
                       creative_id=creative_id,
                       ad_type=ad_type,
                       ad=ad_name,
                       bid=bid,
                       i_url=i_url,
                       adx_status=adx_status)
        ad_object.save()
        return ad_object
