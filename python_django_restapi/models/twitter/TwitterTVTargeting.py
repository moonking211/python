from django.db import models
from django.utils.http import int_to_base36
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager
from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error
from django.conf import settings


class TwitterTVMarketManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterTVMarketManager, self).own(queryset)
        return queryset


class TwitterTVMarket(BaseModel):
    tw_tv_market_id = models.IntegerField(primary_key=True)
    country_code = models.CharField(max_length=2)
    name = models.CharField(max_length=30)
    locale = models.CharField(max_length=7)
    objects = TwitterTVMarketManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_tv_market'
        app_label = 'restapi'

    @classmethod
    def fetch_tv_markets(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')

        if isinstance(account_id,(int,long)):
            account_id = int_to_base36(account_id)

        if account_id is None:
            res = {
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            resource = '/%s/targeting_criteria/tv_markets' % settings.TW_API_VERSION
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']
            res['success'] = True

        except Error as e:
            code = None
            if e.code:
                code = e.code
            elif e.details[0]['code']:
                code = e.details[0]['code']
            res = {
                'data': {},
                'success': False,
                'message': e.details[0]['message'] if e.details and e.details[0] and e.details[0]['message'] else '',
                'errors': { str(code): True } if code else {}
            }
        except Exception as e:
            res = {
                'success': False,
                'message': str(e)
            }
        return res


class TwitterTVGenreManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterTVGenreManager, self).own(queryset)
        return queryset


class TwitterTVGenre(BaseModel):
    tw_targeting_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)

    objects = TwitterTVGenreManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_tv_genre'
        app_label = 'restapi'

    @classmethod
    def fetch_tv_genres(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')

        if isinstance(account_id,(int,long)):
            account_id = int_to_base36(account_id)

        if account_id is None:
            res = {
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            resource = '/%s/targeting_criteria/tv_genres' % settings.TW_API_VERSION
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']
            res['success'] = True

        except Error as e:
            code = None
            if e.code:
                code = e.code
            elif e.details[0]['code']:
                code = e.details[0]['code']
            res = {
                'data': {},
                'success': False,
                'message': e.details[0]['message'] if e.details and e.details[0] and e.details[0]['message'] else '',
                'errors': { str(code): True } if code else {}
            }
        except Exception as e:
            res = {
                'success': False,
                'message': str(e)
            }
        return res


class TwitterTVMarketChannel(models.Model):
    tw_tv_channel = models.ForeignKey('TwitterTVChannel')
    tw_tv_market = models.ForeignKey('TwitterTVMarket')

    class Meta:
        auto_created = True
        db_table = 'tw_tv_market_channel'
        app_label = 'restapi'


class TwitterTVChannelManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterTVChannelManager, self).own(queryset)
        return queryset


class TwitterTVChannel(BaseModel):
    tw_targeting_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    tv_markets = models.ManyToManyField(TwitterTVMarket, through=TwitterTVMarketChannel, related_name="tv_channels")

    objects = TwitterTVChannelManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_tv_channel'
        app_label = 'restapi'

    @classmethod
    def fetch_tv_genres(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        tv_market_id = data.get('tw_tv_market_id')


        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, settings.TW_ACCESS_TOKEN,
                        settings.TW_ACCESS_SECRET)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            tv_market = TwitterTVMarket.objects.get(pk=tv_market_id)
            resource = '/%s/targeting_criteria/tv_channels?tv_market_locale=%s' % (settings.TW_API_VERSION, tv_market.locale)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": "", "endpoint": resource})

            res['data'] = response.body['data']
            res['success'] = True

        except Error as e:
            code = None
            if e.code:
                code = e.code
            elif e.details[0]['code']:
                code = e.details[0]['code']
            res = {
                'data': {},
                'success': False,
                'message': e.details[0]['message'] if e.details and e.details[0] and e.details[0]['message'] else '',
                'errors': { str(code): True } if code else {}
            }
        except Exception as e:
            res = {
                'success': False,
                'message': str(e)
            }
        return res


