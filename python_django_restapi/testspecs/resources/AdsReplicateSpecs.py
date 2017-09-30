from mock import Mock
from mng.test import spec
from rest_framework.status import HTTP_200_OK
from rest_framework.exceptions import ValidationError

from restapi.models.choices import STATUS_ENABLED, STATUS_PAUSED
from restapi.views.ad.AdsReplicate import AdsReplicate
from restapi.testspecs.CreateTestData import CreateTestData


class AdsReplicateSpecs(spec(AdsReplicate), CreateTestData):
    subject = None
    request = None

    campaign = None
    ad_group = None
    ad_group1 = None
    ad1 = None

    # pylint: disable=invalid-name
    ad = None

    def before_each(self):
        self._create_client()

        self.campaign = self.create_campaign()
        self.ad_group = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group')
        self.ad_group1 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 1')

        self.ad1 = self.create_ad(campaign_id=self.ad_group.campaign_id, ad_group_id=self.ad_group,
                                  ad_name='ad 1', size='300x250', status=STATUS_ENABLED)

        ads_replicate_service = Mock()
        request = Mock()
        request.query_params = {}
        request.QUERY_PARAMS = {}

        self.request = request
        self.subject = AdsReplicate(ads_replicate_service=lambda: ads_replicate_service)

    def test__post__creates_copies_of_specified_ads(self):
        self.assertTrue(self.ad_group.ad_set.count() == 1)
        self.assertTrue(self.ad_group1.ad_set.count() == 0)

        self.request.DATA = self.__get_request_data()
        response = self.subject.post(self.request)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.ad_group1.ad_set.count() == 1)
        copied_ad = self.ad_group1.ad_set.first()

        self.assertEqual(copied_ad.campaign_id, self.ad1.ad_group_id.campaign_id.campaign_id)
        self.assertEqual(copied_ad.adx_status, 'new')
        self.assertEqual(copied_ad.appnexus_status, 'new')
        self.assertEqual(copied_ad.a9_status, 'passed')
        self.assertEqual(copied_ad.status, STATUS_ENABLED)
        self.assertEqual(copied_ad.size, self.ad1.size)

    def test__post__creates_existing_copies(self):
        self.assertTrue(self.ad_group.ad_set.count() == 1)
        self.assertTrue(self.ad_group1.ad_set.count() == 0)
        self.request.DATA = self.__get_request_data()

        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertRaises(ValidationError, self.subject.post, self.request)
        self.assertTrue(self.ad_group1.ad_set.count() == 1)

    def __get_request_data(self):
        return {
            'src_ad_group_id': self.ad_group.pk,
            'src_ad_ids': [self.ad1.pk],
            'src_ad_statuses': [STATUS_ENABLED],
            'dst_ad_group_ids': [self.ad_group1.pk],
            'retain_ads_status': 'true',
            'all_enabled_ads': 'false',
            'all_paused_ads': 'false'
        }
