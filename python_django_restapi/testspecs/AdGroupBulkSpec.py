from rest_framework.exceptions import ValidationError

from restapi.models.AdGroup import AdGroup
from restapi.testspecs.CreateTestData import CreateTestData
from restapi.views.ad_group.AdGroupBulk import AdGroupBulk
import json

from mng.test import spec
from mock import Mock


class AdGroupBulkSpec(spec(AdGroupBulk), CreateTestData):
    ad_group_bulk_service = None
    advertiser = None
    campaign = None
    campaign1 = None
    ad_group1 = None
    ad_group2 = None
    ad_group3 = None

    request = None
    subject = None
    frequency_map = json.dumps({"*": "1/28800", "0x0": "3/86400", "320x50": "1/7200", "728x90": "1/7200"})
    frequency_interval = 1
    max_frequency = 2

    def before_each(self):
        self._create_client()

        self.advertiser = self.create_advertiser()

        self.campaign = self.create_campaign(advertiser_id=self.advertiser, campaign_name='campaign_1')
        self.campaign1 = self.create_campaign(advertiser_id=self.advertiser, campaign_name='campaign_2')

        self.ad_group1 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 1')
        self.ad_group2 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 2')

        ad_group_service = Mock()
        request = Mock()
        request.QUERY_PARAMS = {}

        self.request = request
        self.ad_group_bulk_service = ad_group_service
        self.subject = AdGroupBulk(ad_group_service=lambda: ad_group_service)

    def test__post__ad_group_bulk_edit(self):
        #FIXME: restore this test
        return
        # pylint: disable=no-member
        self.assertEqual(2, AdGroup.objects.count())

        self.request.DATA = self._get_request_date(self.ad_group1, self.ad_group2, self.campaign1)
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, 200)

        # pylint: disable=no-member
        self.assertEqual(3, AdGroup.objects.count())

        for entry in list(AdGroup.objects.all()):
            self.assertEqual(entry.status, 'paused')

    def test__post__ad_bulk_edit_validation_error(self):
        # pylint: disable=no-member
        self.assertEqual(2, AdGroup.objects.count())

        self.request.DATA = self._get_request_date(self.ad_group1, self.ad_group2, self.campaign)
        self.assertRaises(ValidationError, self.subject.post, self.request)

        # Without transaction should be 5 rows but after roll back stay 3 as into begining
        # pylint: disable=no-member
        self.assertEqual(2, AdGroup.objects.count())

    # pylint: disable=no-self-use
    def _get_request_date(self, ad_group1, ad_group2, campaign):
        return {
            'delete': [],
            'patch': [
                {
                    "id": ad_group1.ad_group_id,
                    "campaign_id": ad_group1.campaign_id_id,
                    "frequency_map": self.frequency_map,
                    "frequency_interval": self.frequency_interval,
                    "max_frequency": self.max_frequency,
                    "inflator_text": "* 1",
                    "targeting": "",
                    "event_args": "",
                    "flight_start_date": '2014-12-24T14:00:00Z',
                    "flight_end_date": '2014-12-31T23:00:00Z',
                    "parent_name": "",
                    "ad_group": "ad_group1_test",
                    "ad_group_type": 0,
                    "categories": "",
                    "domain": "",
                    "notes": "",
                    "redirect_url": "",
                    "revmap_rev_type": 'click',
                    "revmap_rev_value": '0.00',
                    "revmap_opt_type": 'click',
                    "revmap_opt_value": '0.00',
                    "priority": 0,
                    "daily_budget_type": "",
                    "daily_budget_value": "0.00",
                    "daily_spend": "0.00",
                    "capped": 'false',
                    "hourly_capped": 'false',
                    "status": "paused",
                    "tag": 'null',
                    "flight_budget_type": "",
                    "flight_budget_value": "0.00",
                    "bidder_args": "",
                    "last_update": "2015-08-17T15:26:29Z",
                    "total_cost_cap": "0.00",
                    "daily_cost_cap": "0.00",
                    "total_loss_cap": "0.00",
                    "daily_loss_cap": "0.00"
                },
                {
                    "id": ad_group2.ad_group_id,
                    "campaign_id": ad_group2.campaign_id_id,
                    "frequency_map": self.frequency_map,
                    "frequency_interval": self.frequency_interval,
                    "max_frequency": self.max_frequency,
                    "inflator_text": "* 1",
                    "targeting": "",
                    "event_args": "",
                    "flight_start_date": '2014-12-24T14:00:00Z',
                    "flight_end_date": '2014-12-31T23:00:00Z',
                    "parent_name": "",
                    "ad_group": "ad_group_test",
                    "ad_group_type": 0,
                    "categories": "",
                    "domain": "",
                    "notes": "",
                    "redirect_url": "",
                    "revmap_rev_type": 'click',
                    "revmap_rev_value": '0.00',
                    "revmap_opt_type": 'click',
                    "revmap_opt_value": '0.00',
                    "priority": 0,
                    "daily_budget_type": "",
                    "daily_budget_value": "0.00",
                    "daily_spend": "0.00",
                    "capped": 'false',
                    "hourly_capped": 'false',
                    "status": "paused",
                    "tag": 'null',
                    "flight_budget_type": "",
                    "flight_budget_value": "0.00",
                    "bidder_args": "",
                    "last_update": "2015-08-17T15:26:29Z",
                    "total_cost_cap": "0.00",
                    "daily_cost_cap": "0.00",
                    "total_loss_cap": "0.00",
                    "daily_loss_cap": "0.00"
                }
            ],
            'save': [
                {
                    "campaign_id": campaign.campaign_id,
                    "frequency_map": self.frequency_map,
                    "frequency_interval": self.frequency_interval,
                    "max_frequency": self.max_frequency,
                    "inflator_text": "* 1",
                    "targeting": "",
                    "event_args": "",
                    "flight_start_date": '2014-12-24T14:00:00Z',
                    "flight_end_date": '2014-12-31T23:00:00Z',
                    "parent_name": "",
                    "ad_group": "ad_group_test",
                    "ad_group_type": 0,
                    "categories": "",
                    "domain": "",
                    "notes": "",
                    "redirect_url": "",
                    "revmap_rev_type": 'click',
                    "revmap_rev_value": '0.00',
                    "revmap_opt_type": 'click',
                    "revmap_opt_value": '0.00',
                    "priority": 0,
                    "daily_budget_type": "",
                    "daily_budget_value": "0.00",
                    "daily_spend": "0.00",
                    "capped": 'false',
                    "hourly_capped": 'false',
                    "status": "paused",
                    "tag": 'null',
                    "flight_budget_type": "",
                    "flight_budget_value": "0.00",
                    "bidder_args": "",
                    "last_update": "2015-08-17T15:26:29Z",
                    "total_cost_cap": "0.00",
                    "daily_cost_cap": "0.00",
                    "total_loss_cap": "0.00",
                    "daily_loss_cap": "0.00"
                }
            ]
        }
