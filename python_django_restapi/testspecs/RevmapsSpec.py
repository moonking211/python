from django.utils.timezone import now
from mock import Mock
from decimal import Decimal
from rest_framework.status import HTTP_200_OK
from mng.test import spec

from restapi.views.revmap.RevmapsUpdateAll import RevmapsUpdateAll
from restapi.models.Revmap import Revmap
from restapi.models.AdGroup import AdGroup
from restapi.testspecs.CreateTestData import CreateTestData


class RevmapsSpec(spec(RevmapsUpdateAll), CreateTestData):
    subject = None
    revmap_service = None
    request = None
    revmap_list = None
    campaign = None
    ad_group1 = None
    ad_group2 = None
    ad_group3 = None
    ad_group4 = None

    opt_type = 'install'
    opt_value = Decimal('12345.6789')
    rev_type = 'install'
    rev_value = Decimal('12345.6789')
    target_type = 'install'
    target_value = Decimal('12345.6789')
    last_update = now()

    def before_each(self):
        self._create_client()
        self.campaign = self.create_campaign()

        self.ad_group1 = AdGroup(campaign_id=self.campaign, ad_group='ad group 1', inflator_text='* 1.00')
        self.ad_group1.save()

        self.ad_group2 = AdGroup(campaign_id=self.campaign, ad_group='ad group 2', inflator_text='* 1.00')
        self.ad_group2.save()

        self.ad_group3 = AdGroup(campaign_id=self.campaign, ad_group='ad group 3', inflator_text='* 1.00')
        self.ad_group3.save()

        self.ad_group4 = AdGroup(campaign_id=self.campaign, ad_group='ad group 4', inflator_text='* 1.00')
        self.ad_group4.save()

        self.__create_entry(self.ad_group1, 53)
        self.__create_entry(self.ad_group2, 53)
        self.__create_entry(self.ad_group3, 53)

        revmap_service = Mock()
        request = Mock()
        request.query_params = {}
        request.QUERY_PARAMS = {}

        self.request = request
        self.revmap_service = revmap_service
        self.subject = RevmapsUpdateAll(revmap_service=lambda: revmap_service)

    def test__post__update_all_fields(self):
        # act
        self.request.DATA = {
            u'ad_group_ids': [self.ad_group1.pk, self.ad_group2.pk, self.ad_group3.pk, self.ad_group4.pk],
            u'opt_type': u'install',
            u'opt_value': u'12345.5555',
            u'rev_type': u'install',
            u'rev_value': u'12345.6666',
            u'target_type': u'install',
            u'target_value': u'12345.7777'
        }
        response = self.subject.post(self.request)
        # assert
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test__post__update_two_fields(self):
        self.request.DATA = {
            u'ad_group_ids': [self.ad_group1.pk, self.ad_group2.pk, self.ad_group3.pk],
            u'opt_type': u'click',
            u'opt_value': u'12345.8888'
        }
        response = self.subject.post(self.request)
        # assert
        self.assertEqual(response.status_code, HTTP_200_OK)

        src_ad_group_ids = [long(x) for x in self.request.DATA['ad_group_ids']]

        for ad_group_id in src_ad_group_ids:
            revmap = Revmap.objects.get(ad_group_id=ad_group_id)
            self.assertEqual('click', revmap.opt_type)
            self.assertEqual(Decimal('12345.8888'), revmap.opt_value)

    def test__post__create_entry(self):
        self.assertRaises(Revmap.DoesNotExist, Revmap.objects.get, ad_group_id=self.ad_group4.pk)
        self.__create_entry(self.ad_group4, self.campaign.pk)

        revmap = Revmap.objects.get(ad_group_id=self.ad_group4.pk)
        self.assertIsNotNone(revmap)
        self.assertEqual(self.ad_group4.pk, revmap.ad_group_id.pk)
        self.assertEqual(self.ad_group4.ad_group, revmap.ad_group)
        self.assertEqual(self.campaign.pk, revmap.campaign_id)

    def __create_entry(self, ad_group, campaign_id):
        revmap = Revmap(ad_group_id=ad_group,
                        ad_group=ad_group.ad_group,
                        campaign_id=campaign_id,
                        campaign=self.campaign.campaign,
                        opt_type=self.opt_type,
                        opt_value=self.opt_value,
                        rev_type=self.rev_type,
                        rev_value=self.rev_value,
                        target_type=self.target_type,
                        target_value=self.target_value,
                        last_update=self.last_update)
        revmap.save()

        return revmap
