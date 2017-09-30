from rest_framework.status import HTTP_200_OK
from restapi.models.Ad import Ad
from restapi.views.ad.AdBulk import AdBulk

from restapi.testspecs.CreateTestData import CreateTestData
from mng.test import spec
from mock import Mock


class AdsBulkSpec(spec(AdBulk), CreateTestData):
    subject = None
    ad_service = None
    request = None
    advertiser = None
    campaign = None
    ad_group = None
    ad_base = None

    ad_type = 1
    encrypted_ad_id = 'HcMSVtnbTX6FZS1OcaBwwQ'
    creative_id = 1
    size = '300x250'
    redirect_url = 'http://itunes.apple.com/app/imob-2/id490367305?mt=8'
    i_url = 'http://itunes.2apple.com/app/imob-2/id490367305?mt=8'
    inflator_text = 'Burstly 1.00\nAppSponsor 1.00\n* 0.00'

    def before_each(self):
        self._create_client()
        self.ad_group = self.create_ad_group()

        self.ad_base = Ad(ad_group_id=self.ad_group, creative_id=0, ad_type=-0, ad='ad 1', bid=0, i_url='google.com')
        self.ad_base.save()

        ad_service = Mock()
        request = Mock()
        request.QUERY_PARAMS = {}

        self.request = request
        self.ad_service = ad_service
        self.subject = AdBulk(ad_service=lambda: ad_service)

    def test__post__ad_bulk_upload_edit(self):
        # pylint: disable=no-member
        self.assertEqual(1, Ad.objects.count())
        self.request.DATA = self.__request_data(self.ad_group, self.ad_base)

        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(3, Ad.objects.count())

        # pylint: disable=invalid-name
        for ad in list(Ad.objects.all()):
            self.assertEqual(ad.ad_group_id.ad_group_id, self.ad_group.pk)
            self.assertEqual(ad.ad_type, self.ad_type)
            self.assertEqual(ad.campaign_id, self.ad_group.campaign_id.campaign_id)
            self.assertEqual(ad.creative_id, self.creative_id)
            self.assertEqual(ad.size, self.size)
            self.assertEqual(ad.redirect_url, self.redirect_url)
            self.assertEqual(ad.i_url, self.i_url)
            self.assertEqual(ad.inflator_text, self.inflator_text)

    def test__post__ad_bulk_delete(self):
        ad1 = Ad(ad_group_id=self.ad_group, creative_id=0, ad_type=-0, ad='ad 2', bid=0, i_url='google.com')
        ad1.save()

        # pylint: disable=no-member
        self.assertEqual(2, Ad.objects.count())
        self.request.DATA = {'delete': [self.ad_base.pk, ad1.pk], 'save': []}
        response = self.subject.post(self.request)

        self.assertEqual(response.status_code, HTTP_200_OK)
        # pylint: disable=no-member
        self.assertEqual(0, Ad.objects.count())

        # pylint: disable=invalid-name
    def __request_data(self, ad_group, ad):
        return {'delete': [],
                'save': [
                    {
                        "id": ad.pk,
                        "ad_group_id": ad_group.pk,
                        "ad_type": self.ad_type,
                        "campaign_id": ad_group.campaign_id.campaign_id,
                        "encrypted_ad_id": self.encrypted_ad_id,
                        "creative_id": self.creative_id,
                        "ad": "iMob_300x250_2Girls",
                        "size": self.size,
                        "html": "<a href=\"{CLICK_URL}\"></a>",
                        "preview_html": "<a href=\"{CLICK_URL}\"></a>",
                        "bid": "0.000000",
                        "targeting": "",
                        "categories": "",
                        "attrs": "",
                        "inflator_text": self.inflator_text,
                        "domain": "machinezone.com",
                        "redirect_url": self.redirect_url,
                        "status": "enabled",
                        "adx_status": "new",
                        "appnexus_status": "new",
                        "a9_status": "passed",
                        "external_args": "",
                        "adx_sensitive_categories": "",
                        "adx_product_categories": "",
                        "last_update": "2015-08-14T18:05:27",
                        "i_url": self.i_url,
                        "created_time": "2015-08-14T18:05:27",
                        "adx_attrs": "",
                        "tag": ""
                    },
                    {
                        "ad_group_id": ad_group.pk,
                        "ad_type": self.ad_type,
                        "campaign_id": ad_group.campaign_id.campaign_id,
                        "encrypted_ad_id": self.encrypted_ad_id,
                        "creative_id": self.creative_id,
                        "ad": "iMob_300x250_2Girls_1",
                        "size": self.size,
                        "html": "<a href=\"{CLICK_URL}\"></a>",
                        "preview_html": "<a href=\"{CLICK_URL}\"></a>",
                        "bid": "0.000000",
                        "targeting": "",
                        "categories": "",
                        "attrs": "",
                        "inflator_text": self.inflator_text,
                        "domain": "machinezone.com",
                        "redirect_url": self.redirect_url,
                        "status": "enabled",
                        "adx_status": "new",
                        "appnexus_status": "new",
                        "a9_status": "passed",
                        "external_args": "",
                        "adx_sensitive_categories": "",
                        "adx_product_categories": "",
                        "last_update": "2015-08-14T18:05:27",
                        "i_url": self.i_url,
                        "created_time": "2015-08-14T18:05:27",
                        "adx_attrs": "",
                        "tag": ""
                    },
                    {
                        "ad_group_id": ad_group.pk,
                        "ad_type": self.ad_type,
                        "campaign_id": ad_group.campaign_id.campaign_id,
                        "encrypted_ad_id": self.encrypted_ad_id,
                        "creative_id": self.creative_id,
                        "ad": "iMob_300x250_2Girls_2",
                        "size": self.size,
                        "html": "<a href=\"{CLICK_URL}\"></a>",
                        "preview_html": "<a href=\"{CLICK_URL}\"></a>",
                        "bid": "0.000000",
                        "targeting": "",
                        "categories": "",
                        "attrs": "",
                        "inflator_text": self.inflator_text,
                        "domain": "machinezone.com",
                        "redirect_url": self.redirect_url,
                        "status": "enabled",
                        "adx_status": "new",
                        "appnexus_status": "new",
                        "a9_status": "passed",
                        "external_args": "",
                        "adx_sensitive_categories": "",
                        "adx_product_categories": "",
                        "last_update": "2015-08-14T18:05:27",
                        "i_url": self.i_url,
                        "created_time": "2015-08-14T18:05:27",
                        "adx_attrs": "",
                        "tag": ""
                    }
                ]}
