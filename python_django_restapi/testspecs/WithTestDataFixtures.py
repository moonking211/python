from home.models import User
from restapi.models.Ad import Ad
from restapi.models.Advertiser import Advertiser
from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup
from restapi.registry import REGISTRY


class EntityFactory(object):
    #pylint: disable=no-self-use
    def create_advertiser(self):
        obj = Advertiser()
        obj.save()
        return obj

    #pylint: disable=no-self-use
    def create_campaign(self, **kwargs):
        obj = Campaign()
        obj.campaign = 'Campaign' + _str_rand()
        for key, value in kwargs.iteritems():
            setattr(obj, key, value)
        obj.save()
        return obj

    #pylint: disable=no-self-use
    def create_ad_group(self, **kwargs):
        obj = AdGroup()
        obj.ad_group = 'USA - Display AdGroup - ' + _str_rand()
        obj.notes = ''
        obj.targeting = '{"country":["USA"],"model":"iPhone"}'
        obj.categories = ''
        obj.domain = ''
        obj.redirect_url = ''
        obj.inflator = "* 1"  # inflator_text
        obj.priority = 0
        obj.daily_budget_type = 'revenue'
        obj.daily_budget_value = 300.00
        obj.daily_spend = 100.00
        obj.capped = 0
        obj.hourly_capped = 0
        obj.status = 'enabled'
        obj.tag = ''
        obj.flight_start_date = '2100-10-20 10:00:00'
        obj.flight_end_date = '2100-10-20 10:00:00'
        obj.sampling_rate = 0.0
        obj.throttling_rate = 0.0
        obj.max_frequency = 0
        obj.frequency_interval = 0
        obj.frequency_map = ''
        obj.event_args = ''
        obj.bidder_args = ''
        obj.last_update = '2015-05-05 15:15:15'
        obj.ad_group_type = 1
        obj.targeting_link = None
        for key, value in kwargs.iteritems():
            setattr(obj, key, value)
        obj.save()
        return obj

    def create_ad(self, **kwargs):
        campaign_id_id = kwargs['campaign_id_id']
        # pylint: disable=invalid-name
        ad = kwargs['ad']
        obj = Ad()
        obj.ad_type = 1
        obj.creative_id = None
        obj.size = '320x480'
        # pylint: disable=line-too-long
        obj.html = '<a href="{{CLICK_URL}}"><img src="http://cdn.manage.com/{0}/{1}.gif" width="320" height="480"></a>'.format(campaign_id_id, ad)
        obj.preview_html = '' + obj.html
        obj.bid = 0.0
        obj.targeting = '{"country":["USA"],"model":"iPhone"}'
        obj.categories = ''
        obj.attr = '1001'
        obj.inflator_text = '* 1'
        obj.domain = ''
        obj.redirect_url = ''
        obj.status = 'enabled'
        obj.adx_status = 'new'
        obj.appnexus_status = 'new'
        obj.a9_status = 'passed'
        obj.external_args = ''
        obj.adx_sensitive_categories = ''
        obj.adx_product_categories = ''
        obj.i_url = None
        obj.adx_attrs = ''
        obj.tag = ''
        for key, value in kwargs.iteritems():
            setattr(obj, key, value)
        obj.save()
        return obj


class WithTestDataFixtures(object):
    #pylint: disable=invalid-name
    df = lambda: None

    def before_each(self):
        user = User.objects.create_superuser('testfixture', 'fixture@email.net' 'testfixture', 'testfixture')
        REGISTRY['user'] = user
        request = lambda: None
        request.user = user
        #pylint: disable=invalid-name
        self.df = lambda: None
        self._fill_df(request, self, EntityFactory())

    @staticmethod
    #pylint: disable=invalid-name
    def _fill_df(request, x, f):
        x.df = lambda: None
        x.df.request = request
        #pylint: disable=invalid-name
        df = x.df
        df.advertisers = [
            f.create_advertiser()
        ]
        df.campaigns = [
            f.create_campaign(advertiser_id_id=df.advertisers[0].pk)
        ]
        df.ad_groups = [
            f.create_ad_group(campaign_id_id=df.campaigns[0].pk, status='enabled'),
            f.create_ad_group(campaign_id_id=df.campaigns[0].pk, status='paused'),
            f.create_ad_group(campaign_id_id=df.campaigns[0].pk, status='archived')
        ]
        df.ads = [
            f.create_ad(ad_group_id_id=df.ad_groups[0].pk,
                        campaign_id_id=df.campaigns[0].pk,
                        ad='primusa_320x480_enabled',
                        status='enabled'),
            f.create_ad(ad_group_id_id=df.ad_groups[0].pk,
                        campaign_id_id=df.campaigns[0].pk,
                        ad='secundo_320x480_paused',
                        status='paused'),
            f.create_ad(ad_group_id_id=df.ad_groups[0].pk,
                        campaign_id_id=df.campaigns[0].pk,
                        ad='tertius_320x480_deleted',
                        status='archived')
        ]




def _next_gen():
    i = 1
    while True:
        i += 1
        yield str(i)

#pylint: disable=invalid-name
_str_rand = _next_gen().next
