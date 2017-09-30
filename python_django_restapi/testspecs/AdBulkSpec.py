from rest_framework.exceptions import ValidationError
from restapi.testspecs.CreateTestData import CreateTestData
from restapi.views.ad.AdBulk import AdBulk
from restapi.models.Ad import Ad

from mng.test import spec
from mock import Mock


class AdBulkSpec(spec(AdBulk), CreateTestData):
    ad_bulk_service = None
    campaign = None
    ad_group1 = None
    ad_group2 = None
    ad_group3 = None
    ad_group4 = None
    ad1 = None
    ad2 = None
    ad3 = None

    request = None
    subject = None
    html = '<a href="{CLICK_URL}">' \
           '<img src="https://cdn.manage.com/71/iMob_300x250_2Girls.jpg" width="300" height="250"></a>'

    def before_each(self):
        self._create_client()
        self.campaign = self.create_campaign()

        self.ad_group1 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 1')
        self.ad_group2 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 2')
        self.ad_group3 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 3')
        self.ad_group4 = self.create_ad_group(campaign_id=self.campaign, ad_group_name='ad group 4')

        self.ad1 = self.create_ad(ad_group_id=self.ad_group1, ad_name='ad 1')
        self.ad2 = self.create_ad(ad_group_id=self.ad_group2, ad_name='ad 2')
        self.ad3 = self.create_ad(ad_group_id=self.ad_group3, ad_name='ad 3')

        self.create_revmap(ad_group_id=self.ad_group1, campaign_id=self.campaign.campaign_id)
        self.create_revmap(ad_group_id=self.ad_group2, campaign_id=self.campaign.campaign_id)
        self.create_revmap(ad_group_id=self.ad_group3, campaign_id=self.campaign.campaign_id)
        self.create_revmap(ad_group_id=self.ad_group4, campaign_id=self.campaign.campaign_id)

        ad_service = Mock()
        request = Mock()
        request.query_params = {}
        request.QUERY_PARAMS = {}

        self.request = request
        self.ad_bulk_service = ad_service
        self.subject = AdBulk(ad_service=lambda: ad_service)

    def test__post__ad_bulk_edit(self):
        # pylint: disable=no-member
        self.assertEqual(3, Ad.objects.count())

        self.request.DATA = \
            {
                'delete': [],
                'save': [
                    {
                        'ad_group_id': self.ad_group4.ad_group_id,
                        'ad_type': 1,
                        'campaign_id': 71,
                        'encrypted_ad_id': 'HcMSVtnbTX6FZS1OcaBwwQ',
                        'creative_id': 0,
                        'ad': 'ad 4',
                        'size': '300x250',
                        'html': self.html,
                        'preview_html': '<a></a>',
                        'bid': '1.000000',
                        'targeting': '',
                        'categories': '',
                        'attrs': '',
                        'inflator_text': '1',
                        'domain': 'machinezone.com',
                        'redirect_url': 'https://itunes.apple.com/app/imob-2/id490367305?mt=8',
                        'status': 'enabled',
                        'adx_status': 'new',
                        'appnexus_status': 'new',
                        'a9_status': 'passed',
                        'external_args': '',
                        'adx_sensitive_categories': '',
                        'adx_product_categories': '',
                        'last_update': '2015-05-23T03:11:19',
                        'i_url': 'http://google.com',
                        'created_time': '2015-05-23T03:11:19',
                        'adx_attrs': '',
                        'tag': ''
                    },
                    {
                        'id': self.ad1.pk,
                        'ad_group_id': self.ad1.ad_group_id.ad_group_id,
                        'ad_type': 1,
                        'campaign_id': 71,
                        'encrypted_ad_id': 'HcMSVtnbTX6FZS1OcaBwwQ',
                        'creative_id': 0,
                        'ad': 'ad 1',
                        'size': '300x250',
                        'html': self.html,
                        'preview_html': '<a></a>',
                        'bid': '1.000000',
                        'targeting': '',
                        'categories': '',
                        'attrs': '',
                        'inflator_text': '1',
                        'domain': 'machinezone.com',
                        'redirect_url': 'https://itunes.apple.com/app/imob-2/id490367305?mt=8',
                        'status': 'enabled',
                        'adx_status': 'new',
                        'appnexus_status': 'new',
                        'a9_status': 'passed',
                        'external_args': '',
                        'adx_sensitive_categories': '',
                        'adx_product_categories': '',
                        'last_update': '2015-05-23T03:11:19',
                        'i_url': 'http://google.com/',
                        'created_time': '2015-05-23T03:11:19',
                        'adx_attrs': '',
                        'tag': ''
                    },
                    {
                        'id': self.ad2.pk,
                        'ad_group_id': self.ad2.ad_group_id.ad_group_id,
                        'ad_type': 1,
                        'campaign_id': 71,
                        'encrypted_ad_id': 'bE1s9a4HlXrP9hUkBLAGHA',
                        'creative_id': 0,
                        'ad': 'ad 2',
                        'size': '300x250',
                        'html': self.html,
                        'preview_html': '<a></a>',
                        'bid': '1.000000',
                        'targeting': '',
                        'categories': '',
                        'attrs': '',
                        'inflator_text': '1',
                        'domain': 'machinezone.com',
                        'redirect_url': 'https://itunes.apple.com/app/imob-2/id490367305?mt=8',
                        'status': 'enabled',
                        'adx_status': 'new',
                        'appnexus_status': 'new',
                        'a9_status': 'passed',
                        'external_args': '',
                        'adx_sensitive_categories': '',
                        'adx_product_categories': '',
                        'last_update': '2015-05-23T03:11:19',
                        'i_url': 'http://google.com/',
                        'created_time': '2015-05-23T03:11:19',
                        'adx_attrs': '',
                        'tag': ''
                    },
                    {
                        'id': self.ad3.pk,
                        'ad_group_id': self.ad3.ad_group_id.ad_group_id,
                        'ad_type': 1,
                        'campaign_id': 71,
                        'encrypted_ad_id': 'D0RLOQbpY2JrYHLmWl43nw',
                        'creative_id': 0,
                        'ad': 'ad 3',
                        'size': '300x250',
                        'html': self.html,
                        'preview_html': '<a></a>',
                        'bid': '1.000000',
                        'targeting': '',
                        'categories': '',
                        'attrs': '',
                        'inflator_text': '1',
                        'domain': 'machinezone.com',
                        'redirect_url': 'https://itunes.apple.com/app/imob-2/id490367305?mt=8',
                        'status': 'enabled',
                        'adx_status': 'new',
                        'appnexus_status': 'new',
                        'a9_status': 'passed',
                        'external_args': '',
                        'adx_sensitive_categories': '',
                        'adx_product_categories': '',
                        'last_update': '2015-05-23T03:11:19',
                        'i_url': 'http://google.com',
                        'created_time': '2015-05-23T03:11:19',
                        'adx_attrs': '',
                        'tag': ''
                    }
                ]
            }
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, 200)

        # pylint: disable=no-member
        self.assertEqual(4, Ad.objects.count())

        for entry in list(Ad.objects.all()):
            self.assertEqual(entry.ad_type, 1)
            self.assertEqual(entry.bid, 1.000000)
            self.assertEqual(entry.redirect_url, 'https://itunes.apple.com/app/imob-2/id490367305?mt=8')

    def test__post__ad_bulk_edit_validation_error(self):
        # pylint: disable=no-member
        self.assertEqual(3, Ad.objects.count())

        self.request.DATA = \
            {
                'delete': [],
                'save': [
                    {
                        'id': self.ad1.pk,
                        'ad_group_id': self.ad1.ad_group_id.ad_group_id,
                        'ad_type': 1,
                        'campaign_id': 71,
                        'encrypted_ad_id': 'bE1s9a4HlXrP9hUkBLAGHA',
                        'creative_id': 0,
                        'ad': 'ad 1',
                        'size': '300x250',
                        'html': self.html,
                        'preview_html': '<a></a>',
                        'bid': '1.000000',
                        'targeting': '',
                        'categories': '',
                        'attrs': '',
                        'inflator_text': '1',
                        'domain': 'machinezone.com',
                        'redirect_url': 'https://itunes.apple.com/app/imob-2/id490367305?mt=8',
                        'status': 'enabled',
                        'adx_status': 'new',
                        'appnexus_status': 'new',
                        'a9_status': 'passed',
                        'external_args': '',
                        'adx_sensitive_categories': '',
                        'adx_product_categories': '',
                        'last_update': '2015-05-23T03:11:19',
                        'i_url': '',
                        'created_time': '2015-05-23T03:11:19',
                        'adx_attrs': '',
                        'tag': ''
                    },
                    {
                        'id': self.ad2.pk,
                        'ad_group_id': self.ad1.ad_group_id.ad_group_id,
                        'ad_type': 1,
                        'campaign_id': 71,
                        'encrypted_ad_id': 'D0RLOQbpY2JrYHLmWl43nw',
                        'creative_id': 0,
                        'ad': 'ad 1',
                        'size': '300x250',
                        'html': '<a></a>',
                        'preview_html': self.html,
                        'bid': '1.000000',
                        'targeting': '',
                        'categories': '',
                        'attrs': '',
                        'inflator_text': '1',
                        'domain': 'machinezone.com',
                        'redirect_url': 'https://itunes.apple.com/app/imob-2/id490367305?mt=8',
                        'status': 'enabled',
                        'adx_status': 'new',
                        'appnexus_status': 'new',
                        'a9_status': 'passed',
                        'external_args': '',
                        'adx_sensitive_categories': '',
                        'adx_product_categories': '',
                        'last_update': '2015-05-23T03:11:19',
                        'i_url': 'h',
                        'created_time': '2015-05-23T03:11:19',
                        'adx_attrs': '',
                        'tag': ''
                    }
                ]
            }
        self.assertRaises(ValidationError, self.subject.post, self.request)

        # Without transaction should be 5 rows but after roll back stay 3 as into begining
        # pylint: disable=no-member
        self.assertEqual(3, Ad.objects.count())
