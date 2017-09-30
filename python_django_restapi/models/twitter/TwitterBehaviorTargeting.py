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


class TwitterBehaviorTaxonomyManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterBehaviorTaxonomyManager, self).own(queryset)
        return queryset


class TwitterBehaviorTaxonomy(BaseModel):
    tw_behavior_taxonomy_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('TwitterBehaviorTaxonomy', null=True, db_column='parent_id')
    US = models.BooleanField(default=False, db_column='US')
    GB = models.BooleanField(default=False, db_column='GB')

    objects = TwitterBehaviorTaxonomyManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_behavior_taxonomy'
        app_label = 'restapi'

    @classmethod
    def fetch_behavior_taxonomies(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            resource = '/{api_version}/targeting_criteria/behavior_taxonomies?count=1000'.format(api_version=settings.TW_API_VERSION)
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


class TwitterBehaviorManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterBehaviorManager, self).own(queryset)
        return queryset


class TwitterBehavior(BaseModel):
    tw_targeting_id = models.BigIntegerField(primary_key=True, null=False)
    tw_behavior_taxonomy = models.ForeignKey('TwitterBehaviorTaxonomy', db_column='tw_behavior_taxonomy_id')
    country_code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    audience_size = models.BigIntegerField(null=True, default=0)
    partner_source = models.CharField(max_length=255)

    objects = TwitterBehaviorManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_behavior'
        app_label = 'restapi'

    @classmethod
    def fetch_behaviors(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')
        country_code = data.get('country_code', 'US')

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
            resource = '/{api_version}/targeting_criteria/behaviors?count=1000&country_code={country_code}'.format(api_version=settings.TW_API_VERSION, country_code=country_code)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']
            next_cursor = response.body.get('next_cursor', False)
            while next_cursor:
                resource = '/{api_version}/targeting_criteria/behaviors?count=1000&cursor={next_cursor}&country_code={country_code}'.format(next_cursor=next_cursor, country_code=country_code, api_version=settings.TW_API_VERSION)
                response = Request(client, 'get', resource).perform()
                next_cursor = response.body.get('next_cursor', False)
                res['data'] += response.body['data']

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