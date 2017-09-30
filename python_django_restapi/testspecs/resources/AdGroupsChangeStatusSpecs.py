from mock import Mock
from mng.test import spec

from rest_framework.status import HTTP_200_OK

from restapi.models.AdGroup import AdGroup
from restapi.models.choices import STATUS_ENABLED, STATUS_PAUSED
from restapi.views.ad_group.AdGroupsChangeStatus import AdGroupsChangeStatus
from restapi.testspecs.CreateTestData import CreateTestData


class AdGroupsChangeStatusSpecs(spec(AdGroupsChangeStatus), CreateTestData):
    subject = None
    ad_group_service = None
    request = None

    campaign = None
    ad_group = None
    ad_group1 = None

    def before_each(self):
        self._create_client()

        self.campaign = self.create_campaign()
        self.ad_group = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group', status=STATUS_PAUSED)
        self.ad_group1 = self.create_ad_group(campaign_id=self.campaign,
                                              ad_group_name='ad group 1', status=STATUS_PAUSED)
        self.ad_group.revmap_rev_value = 1.34
        self.ad_group.revmap_rev_type = 'click'
        self.ad_group.revmap_opt_value = 13.2
        self.ad_group.revmap_opt_type = 'install'
        self.ad_group.targeting = '{"country":["USA"], "os":"Android"}'
        self.ad_group.save()

        self.ad_group1.revmap_rev_value = 11.24
        self.ad_group1.revmap_rev_type = 'click'
        self.ad_group1.revmap_opt_value = 3.21
        self.ad_group1.revmap_opt_type = 'install'
        self.ad_group1.targeting = '{"country":["USA"], "os":"Android"}'
        self.ad_group1.save()

        ad_group_service = Mock()

        request = Mock()
        request.query_params = {}
        request.QUERY_PARAMS = {}

        self.request = request
        self.ad_group_service = ad_group_service
        self.subject = AdGroupsChangeStatus(ad_group_service=lambda: ad_group_service)

    def test__post__set_status_by_ad_id(self):
        self.assertEqual(self.ad_group.status, STATUS_PAUSED)
        self.assertEqual(self.ad_group1.status, STATUS_PAUSED)

        self.request.DATA = {
            u'src_ad_group_ids': [self.ad_group.pk, self.ad_group1.pk],
            u'new_status': u'enabled'
        }

        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(AdGroup.objects.get(pk=self.ad_group.pk).status, STATUS_ENABLED)
        self.assertEqual(AdGroup.objects.get(pk=self.ad_group1.pk).status, STATUS_ENABLED)
