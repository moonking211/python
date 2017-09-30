from mock import Mock
from mng.test import spec
from decimal import Decimal
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from restapi.models.AdGroup import AdGroup
from restapi.models.Revmap import Revmap
from restapi.models.Ad import Ad

from restapi.views.ad_group.AdGroupsReplicate import AdGroupsReplicate
from restapi.testspecs.CreateTestData import CreateTestData


class AdGroupsReplicateSpec(spec(AdGroupsReplicate), CreateTestData):
    ad_group_replicate_service = None

    ad_group1 = None
    ad1 = None
    ad2 = None
    ad3 = None
    revmap1 = None

    subject = None
    request = None

    opt_type = 'install'
    opt_value = Decimal('1.44')
    rev_type = 'install'
    rev_value = Decimal('1.45')
    target_type = 'install'
    target_value = Decimal('1.46')
    last_update = now()

    def before_each(self):
        self._create_client()
        self.ad_group1 = self.create_ad_group()

        self.revmap1 = Revmap(ad_group_id=self.ad_group1,
                              ad_group=self.ad_group1.ad_group,
                              campaign_id=self.ad_group1.campaign_id_id,
                              campaign=self.ad_group1.campaign_id.campaign,
                              opt_type=self.opt_type,
                              opt_value=self.opt_value,
                              rev_type=self.rev_type,
                              rev_value=self.rev_value,
                              target_type=self.target_type,
                              target_value=self.target_value,
                              last_update=self.last_update)
        self.revmap1.save()

        self.ad1 = Ad(ad_group_id=self.ad_group1,
                      size='0x0',
                      ad_type=-0,
                      ad='ad_1', bid=0,
                      i_url='',
                      inflator_text="* 1.00")
        self.ad1.save()

        self.ad2 = Ad(ad_group_id=self.ad_group1,
                      size='0x0',
                      ad_type=-0,
                      ad='ad_2',
                      bid=0,
                      i_url='',
                      inflator_text="* 1.00")
        self.ad2.save()

        self.ad3 = Ad(ad_group_id=self.ad_group1,
                      size='0x0',
                      ad_type=-0,
                      ad='ad_3',
                      bid=0, i_url='',
                      inflator_text="* 1.00")
        self.ad3.save()

        ad_service = Mock()
        request = Mock()
        request.query_params = {}
        request.QUERY_PARAMS = {}
        request.query_params = {}

        self.request = request
        self.ad_group_replicate_service = ad_service
        self.subject = AdGroupsReplicate(ad_service=lambda: ad_service)

    def test__post__ad_group_replicate(self):
        self.assertEqual(1, AdGroup.objects.count())
        self.assertEqual(3, Ad.objects.count())

        self.request.DATA = self.__get_request_data()

        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(9, Ad.objects.count())
        self.assertEqual(3, AdGroup.objects.count())

    def test__post__ad_group_replicate_validation_error(self):
        self.assertEqual(1, AdGroup.objects.count())
        self.assertEqual(3, Ad.objects.count())

        self.ad1.size = '0x9'
        self.ad1.save()

        self.request.DATA = self.__get_request_data()

        self.assertRaises(ValidationError, self.subject.post, self.request)
        self.assertEqual(1, AdGroup.objects.count())
        self.assertEqual(3, Ad.objects.count())

    def test__post__replicate_ad_groups_with_revmap(self):
        self.assertEqual(1, Revmap.objects.count())
        self.assertEqual(1, AdGroup.objects.count())
        self.assertEqual(3, Ad.objects.count())

        self.request.DATA = self.__get_request_data()
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(Revmap.objects.count() == 3)

        for ad_group in list(AdGroup.objects.all()):
            self.assertEqual(ad_group.revmap_rev_type, self.rev_type)
            self.assertEqual(ad_group.revmap_rev_value, self.rev_value)
            self.assertEqual(ad_group.revmap_opt_type, self.opt_type)
            self.assertEqual(ad_group.revmap_opt_value, self.opt_value)
            self.assertEqual(ad_group.revmap_target_type, self.target_type)
            self.assertEqual(ad_group.revmap_target_value, self.target_value)

    def __get_request_data(self):
        return {'new_names': [['clone 1', 'clone 2']],
                'src_ad_group_ids': [self.ad_group1.pk],
                'include_redirect_url': 'true',
                'include_ads': 'true',
                'retain_ads_status': 'true',
                'all_enabled_ads': 'false',
                'all_paused_ads': 'false'}
