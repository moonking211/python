from mock import Mock
from mng.test import spec

from rest_framework.status import HTTP_200_OK

from restapi.views.ad.AdsChangeStatus import AdsChangeStatus
from restapi.models.Ad import Ad
from restapi.models.choices import STATUS_ENABLED, STATUS_PAUSED
from restapi.testspecs.CreateTestData import CreateTestData


class AdsChangeStatusSpecs(spec(AdsChangeStatus), CreateTestData):
    ads_change_status_service = None
    subject = None
    request = None

    ad_group = None
    ad_group1 = None
    ad1 = None
    ad2 = None

    def before_each(self):
        self._create_client()
        self.ad_group = self.create_ad_group()

        self.ad1 = self.create_ad(campaign_id=self.ad_group.campaign_id, ad_group_id=self.ad_group, ad_name='ad 1')
        self.ad2 = self.create_ad(campaign_id=self.ad_group.campaign_id, ad_group_id=self.ad_group, ad_name='ad 2')

        self.ads_change_status_service = Mock()
        self.subject = AdsChangeStatus(ads_change_status_service=lambda: self.ads_change_status_service)

        request = Mock()
        request.query_params = {}
        request.QUERY_PARAMS = {}
        self.request = request

    def test__post__set_status_by_ad_id(self):
        self.assertEqual(self.ad1.status, STATUS_PAUSED)
        self.assertEqual(self.ad2.status, STATUS_PAUSED)

        self.request.DATA = {
            'src_ad_group_id': self.ad_group.pk,
            'src_ad_ids': [self.ad1.pk, self.ad2.pk],
            'src_ad_statuses': [u'paused'],
            'new_status': u'enabled'
        }

        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(Ad.objects.get(pk=self.ad1.pk).status, STATUS_ENABLED)
        self.assertEqual(Ad.objects.get(pk=self.ad2.pk).status, STATUS_ENABLED)

    def test__post__set_status_to_all(self):
        self.assertEqual(self.ad1.status, STATUS_PAUSED)
        self.assertEqual(self.ad2.status, STATUS_PAUSED)

        self.request.DATA = {
            'src_ad_group_id': self.ad_group.pk,
            'src_ad_ids': ['-1'],
            'src_ad_statuses': [u'paused'],
            'new_status': u'enabled'
        }
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(Ad.objects.get(pk=self.ad1.pk).status, STATUS_ENABLED)
        self.assertEqual(Ad.objects.get(pk=self.ad2.pk).status, STATUS_ENABLED)
