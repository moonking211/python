import json

import six

import _mysql_exceptions
from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.models.twitter.TwitterConfig import *
from restapi.models.twitter.TwitterTVTargeting import TwitterTVChannel, TwitterTVGenre
from restapi.models.twitter.TwitterBehaviorTargeting import TwitterBehavior
import twitter
from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error
import urllib
import logging


logger = logging.getLogger('debug')

class TwitterAppCategoryManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterAppCategoryManager, self).own(queryset)
        return queryset


class TwitterAppCategory(BaseModel):
    tw_targeting_id = models.BigIntegerField(primary_key=True)
    platform = models.CharField(max_length=255)
    app_category = models.CharField(max_length=255)

    objects = TwitterAppCategoryManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.app_category

    class Meta:
        db_table = 'tw_app_category'
        app_label = 'restapi'

    @classmethod
    def fetch_app_categories(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/app_store_categories'.format(api_version=settings.TW_API_VERSION)
            response = Request(client, 'get', resource).perform()
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


class TwitterCarrierManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterCarrierManager, self).own(queryset)
        return queryset


class TwitterCarrier(BaseModel):
    tw_targeting_id = models.BigIntegerField(primary_key=True)
    country_code = models.CharField(max_length=2)
    carrier_name = models.CharField(max_length=255)

    objects = TwitterCarrierManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.carrier_name

    class Meta:
        db_table = 'tw_carrier'
        app_label = 'restapi'

    @classmethod
    def fetch_carriers(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/network_operators?count=1000'.format(api_version=settings.TW_API_VERSION)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']

            next_cursor = None
            if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                next_cursor = response.body['next_cursor']
                while next_cursor is not 0:
                    resource = '/{api_version}/targeting_criteria/network_operators?cursor={next_cursor}'.format(api_version=settings.TW_API_VERSION, next_cursor=next_cursor)
                    response = Request(client, 'get', resource).perform()
                    next_cursor = response.body['next_cursor'] or 0
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


class TwitterDeviceManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterDeviceManager, self).own(queryset)
        return queryset


class TwitterDevice(BaseModel):
    tw_targeting_id = models.BigIntegerField(primary_key=True)
    device = models.CharField(max_length=255)
    platform = models.CharField(max_length=255)

    objects = TwitterDeviceManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.device

    class Meta:
        db_table = 'tw_device'
        app_label = 'restapi'

    @classmethod
    def fetch_devices(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/devices'.format(api_version=settings.TW_API_VERSION)
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

class TwitterLocationManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterLocationManager, self).own(queryset)
        return queryset


class TwitterLocation(BaseModel):
    tw_targeting_id = models.CharField(max_length=255, primary_key=True)
    location_type = models.CharField(max_length=255)
    location_name = models.CharField(max_length=255)
    country_code3 = models.CharField(max_length=3)
    export_id = models.CharField(max_length=255)

    objects = TwitterLocationManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.location_name

    class Meta:
        db_table = 'tw_location'
        app_label = 'restapi'

    @classmethod
    def fetch_countries(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/locations?location_type=COUNTRY&count=1000'.format(api_version=settings.TW_API_VERSION)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']

            next_cursor = None
            if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                next_cursor = response.body['next_cursor']
                while next_cursor is not 0:
                    resource = '/{api_version}/targeting_criteria/locations?location_type=COUNTRY&cursor={next_cursor}'.format(api_version=settings.TW_API_VERSION, next_cursor=next_cursor)
                    response = Request(client, 'get', resource).perform()
                    next_cursor = response.body['next_cursor'] or 0
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

class TwitterOsVersionManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterOsVersionManager, self).own(queryset)
        return queryset


class TwitterOsVersion(BaseModel):
    tw_targeting_id = models.IntegerField(primary_key=True)
    platform = models.CharField(max_length=255)
    os_version = models.CharField(max_length=255)
    number = models.CharField(max_length=255)

    objects = TwitterOsVersionManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.os_version

    class Meta:
        db_table = 'tw_os_version'
        app_label = 'restapi'

    @classmethod
    def fetch_os_versions(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/platform_versions'.format(api_version=settings.TW_API_VERSION)
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

class TwitterUserInterestManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterUserInterestManager, self).own(queryset)
        return queryset


class TwitterUserInterest(BaseModel):
    tw_targeting_id = models.IntegerField(primary_key=True)
    category = models.CharField(max_length=255)
    subcategory = models.CharField(max_length=255)

    objects = TwitterUserInterestManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.subcategory

    class Meta:
        db_table = 'tw_user_interest'
        app_label = 'restapi'

    @classmethod
    def fetch_user_interests(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
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
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/interests?count=1000'.format(api_version=settings.TW_API_VERSION)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']

            next_cursor = None
            if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                next_cursor = response.body['next_cursor']
                while next_cursor is not 0:
                    resource = '/{api_version}/targeting_criteria/interests?cursor={next_cursor}&count=1000'.format(api_version=settings.TW_API_VERSION, next_cursor=next_cursor)
                    response = Request(client, 'get', resource).perform()
                    next_cursor = response.body['next_cursor'] or 0
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


class TwitterEventManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterEventManager, self).own(queryset)
        return queryset


class TwitterEvent(BaseModel):
    tw_targeting_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField(primary_key=True)
    end_time = models.DateTimeField(primary_key=True)


    objects = TwitterEventManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_event'
        app_label = 'restapi'

    @classmethod
    def fetch_event_by_id(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')
        event_id = data.get('event_id')

        if isinstance(account_id,(int,long)):
            account_id = int_to_base36(account_id)
        if isinstance(event_id,(int,long)):
            event_id = int_to_base36(event_id)

        if account_id is None:
            res = {
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        if event_id is None:
            res = {
                'success': False,
                'message': "Missing Twitter Event ID"
            }
            return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            account = client.accounts(account_id)
            resource = '/{api_version}/targeting_criteria/events?ids={event_id}'.format(api_version=settings.TW_API_VERSION, event_id=event_id)
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

class TwitterTargetingManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterTargetingManager, self).own(queryset)
        return queryset


class TwitterTargeting(BaseModel):
    tw_criteria_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    tw_line_item = models.ForeignKey(TwitterLineItem, db_column='tw_line_item_id',
                                        related_name="tw_targetings", related_query_name="tw_targeting",)
    tw_targeting_type = models.IntegerField()
    tw_targeting_id = models.CharField(max_length=255)
    targeting_value = models.CharField(max_length=255)
    targeting_params = models.CharField(max_length=255)

    objects = TwitterTargetingManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return "name: %s, tw_line_item: %s, targeting_value: %s, tw_targeting_id: %s" % (self.name, self.tw_line_item_id, self.targeting_value, self.tw_targeting_id)

    class Meta:
        db_table = 'tw_targeting'
        app_label = 'restapi'

    @classmethod
    def get_recommeded_handles(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        handles = data.get('handles')
        number = data.get('number', 40)
        account_id = data.get('account_id')
        if account_id and handles and number:
            try:
                account = TwitterAccount.objects_raw.get(pk=account_id)
                oauth_token = account.tw_twitter_user_id.oauth_token or settings.TW_ACCESS_TOKEN
                oauth_secret = account.tw_twitter_user_id.oauth_secret or settings.TW_ACCESS_SECRET
                if not account_id:
                    return Response([])
                account_id = long(account_id)
                if isinstance(account_id,(int,long)):
                    account_id = int_to_base36(account_id)

                client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                                    oauth_secret)
                if settings.TW_SANDBOX:
                    client.sandbox = settings.TW_SANDBOX

                api_domain = 'https://ads.twitter.com'
                resource = '/accounts/%s/handle_recommendation.json?handles=%s&number=%s' % (account_id, handles, number)
                response = Request(client, 'get', resource, domain=api_domain).perform()
                res = []
                api_domain = 'https://api.twitter.com'
                i = 0
                while i < len(response.body):
                    temp = response.body[i:i+100]
                    i += 100
                    resource = '/1.1/users/lookup.json?screen_name=%s' % ','.join(temp)
                    resource = resource.replace('@', '')
                    result = Request(client, 'get', resource, domain=api_domain).perform()
                    res = res + [dict(id=r['id_str'], screen_name=r['screen_name'],
                                    follower_count=r['followers_count']) for r in result.body]

                return dict(success=True, data=res, msg='')
            except Exception as e:
                return dict(success=False, data=[], msg=str(e))
        else:
            return dict(success=False, data=[], msg='account_id or handles are missing')

    @classmethod
    def get_recommeded_keywords(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        keywords = data.get('keywords')
        number = data.get('number', 40)
        account_id = data.get('account_id')
        if account_id and keywords and number:
            try:
                account = TwitterAccount.objects_raw.get(pk=account_id)
                oauth_token = account.tw_twitter_user_id.oauth_token or settings.TW_ACCESS_TOKEN
                oauth_secret = account.tw_twitter_user_id.oauth_secret or settings.TW_ACCESS_SECRET
                if not account_id:
                    return Response([])
                account_id = long(account_id)
                if isinstance(account_id,(int,long)):
                    account_id = int_to_base36(account_id)

                client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                                oauth_secret)
                if settings.TW_SANDBOX:
                    client.sandbox = settings.TW_SANDBOX

                api_domain = 'https://ads.twitter.com'
                resource = '/accounts/%s/keyword_recommendations.json?keywords=%s&number=%s' % \
                           (account_id, urllib.quote_plus(keywords), number)
                response = Request(client, 'get', resource, domain=api_domain).perform()

                return dict(success=True, data=response.body, msg='')
            except Exception as e:
                return dict(success=False, data=[], msg=str(e))
        else:
            return dict(success=False, data=[], msg='account_id or keywords are missing')

    @classmethod
    def fetch_targeting(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')
        line_item_id = data.get('line_item_id')
        line_item_id_int = None

        if isinstance(line_item_id, six.string_types):
            line_item_id_int = base36_to_int(line_item_id)

        if isinstance(line_item_id,(int,long)):
            line_item_id_int = line_item_id
            line_item_id = int_to_base36(line_item_id)
        else:
            line_item_id_int = base36_to_int(line_item_id)

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id = int_to_base36(account_id)

        if account_id is None:
            res = {
                'data': {},
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        if line_item_id is None:
            res = {
                'data': {},
                'success': False,
                'message': "Missing Twitter Line Item ID"
            }
            return res

        if line_item_id_int is None:
            res = {
                'data': {},
                'success': False,
                'message': "Missing Twitter Line Item ID"
            }
            return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            account = client.accounts(account_id)
            resource = '/{api_version}/accounts/{account_id}/targeting_criteria?line_item_id={line_item_id}&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, line_item_id=line_item_id)
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
                'data': {},
                'success': False,
                'message': str(e)
            }

        if syncData and res['data'] and res['success']:
            res['sync'] = {}
            if isinstance(res['data'], dict):
                res['data'] = [res['data']]

            sync_success   = 0
            sync_fail      = 0
            new_count      = 0
            existing_count = 0
            for index, api_line_item_targeting in enumerate(res['data'], start=0):

                line_item_targeting_res = self.sync_targeting(account_id_int, line_item_id_int, api_line_item_targeting)
                if 'success' in line_item_targeting_res and line_item_targeting_res['success'] is True:
                    if 'skip' in line_item_targeting_res:
                        continue

                    if line_item_targeting_res['type'] == 'existing':
                        existing_count +=1
                    if line_item_targeting_res['type'] == 'new':
                        new_count +=1
                    sync_success += 1
                elif 'success' in line_item_targeting_res and line_item_targeting_res['success'] is False:
                    sync_fail += 1

            res['sync']['type'] = {}
            res['sync']['type']['existing'] = existing_count
            res['sync']['type']['new'] = new_count
            res['sync']['total'] = sync_success
            if sync_fail == 0:
                res['sync']['success'] = True
            else:
                res['sync']['success'] = False

        return res

    @classmethod
    def format_params(self, data, type='new'):
        params = {}
        try:
            # Since we store targeting_value as tw_targeting_id for enum types, we need to set targeting_value before posting to Twitter
            if TW_TARGETING_ID_TO_TYPE[data['tw_targeting_type']] == 'enum' and 'tw_targeting_id' in data:
                data['targeting_value'] = data['tw_targeting_id']
                data['tw_targeting_id'] = ""

            if TW_TARGETING_VALUE_TYPE[data['tw_targeting_type']] == 'base36':
                data['targeting_value'] = int_to_base36(int(data['targeting_value']))
            if TW_TARGETING_VALUE_TYPE[data['tw_targeting_type']] == 'base10':
                data['targeting_value'] = int(data['targeting_value'])
            params['targeting_criterion_id'] = int_to_base36(data['tw_criteria_id']) if 'tw_criteria_id' in data else None
            if type == 'delete' and not params['targeting_criterion_id']:
                params['targeting_criterion_id'] = data['targeting_value']
            if type == 'delete':
                params['id'] = params['targeting_criterion_id']
            params['line_item_id']           = int_to_base36(data['tw_line_item_id']) if 'tw_line_item_id' in data else None
            params['targeting_type']         = TW_TARGETING_ID_TO_ENUM[int(data['tw_targeting_type'])] if 'tw_targeting_type' in data else None
            params['targeting_value']        = data['targeting_value'] if 'targeting_value' in data else None

            #https://twittercommunity.com/t/invalid-operator-type-when-creating-platform-version-targeting-through-v1-endpoint/71874
            if data['tw_targeting_type'] == 16:
                params['operator_type'] = 'GTE'

            # for all audience targetings, make them as excluded
            # https://twittercommunity.com/t/problem-creating-tailored-audience-expansion-exclusion-targeting-with-v1-api/70611/5
            if params['targeting_type'] == 'TAILORED_AUDIENCE':
                if data.get('operator_type'):
                    params['operator_type'] = data['operator_type']
                else:
                    params['operator_type'] = "NE"

            params = dict((k,v) for k,v in params.iteritems() if v is not None and v is not "")
        except Exception as e:
            logger.debug('*' * 50)
            logger.debug('format_params failed')
            logger.debug('exception details')
            logger.debug(str(e))
            logger.debug('_' * 50)
            logger.debug('data details')
            logger.debug(data)
            logger.debug('*' * 50)
            return False

        return params

    @classmethod
    def create(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_targeting(data, account_id, oauth_token, oauth_token_secret, "post")

    @classmethod
    def update(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_targeting(data, account_id, oauth_token, oauth_token_secret, "put")

    @classmethod
    def delete(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_targeting(data, account_id, oauth_token, oauth_token_secret, "delete")

    @classmethod
    def create_update_targeting(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET, request_type="post"):
        res = {}
        res['success'] = False

        account_id_int = account_id
        account_id_base36 = int_to_base36(account_id)
        tw_criteria_id = data.get('tw_criteria_id', None)
        line_item_id = data.get('line_item_id', None)
        line_item_id_base36 = None
        tw_criteria_id_base36 = None

        if line_item_id is not None:
            line_item_id_base36 = int_to_base36(line_item_id)

        if account_id_base36 is None:
            res = {
                'data': {},
                'success': False,
                'message': "Invaid Twitter Account ID"
            }
            return res

        if request_type == 'delete' or request_type == 'put':
            if tw_criteria_id is not None:
                tw_criteria_id_base36 = int_to_base36(tw_criteria_id)
            else:
                res = {
                    'data': {},
                    'success': False,
                    'message': "Missing Twitter Criteria ID"
                }
                return res

        if request_type == 'post':
            if line_item_id_base36 is None:
                res = {
                    'data': {},
                    'success': False,
                    'message': "Missing Twitter Line Item"
                }
                return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            account = client.accounts(account_id_base36)

            if request_type == 'post':
                targeting_value = data['tw_targeting_value']
                targeting_type = TW_TARGETING_ID_TO_ENUM[int(data['tw_targeting_type'])]
                resource = '/{api_version}/accounts/{account_id}/targeting_criteria?line_item_id={line_item_id}&targeting_type={targeting_type}&targeting_value={targeting_value}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, line_item_id=line_item_id_base36, targeting_value=targeting_value, targeting_type=targeting_type)
            elif request_type == 'delete':
                resource = '/{api_version}/accounts/{account_id}/targeting_criteria/{tw_criteria_id}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, tw_criteria_id=tw_criteria_id_base36)
            elif request_type == 'put':
                resource = '/{api_version}/accounts/{account_id}/targeting_criteria?line_item_id={line_item_id}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, line_item_id=line_item_id_base36)

            response = Request(client, request_type, resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            if response.code == 200 or response.code == 201:
                res['success'] = True

            res['data'] = response.body['data']

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
                'data': {},
                'success': False,
                'message': str(e)
            }

        if res['data'] and res['success']:
            res['sync'] = {}
            if isinstance(res['data'], dict):
                res['data'] = [res['data']]

            sync_success   = 0
            sync_fail      = 0
            new_count      = 0
            existing_count = 0
            for index, api_line_item_targeting in enumerate(res['data'], start=0):

                line_item_targeting_res = self.sync_targeting(account_id_int, line_item_id, api_line_item_targeting)
                if 'success' in line_item_targeting_res and line_item_targeting_res['success'] is True:
                    if 'skip' in line_item_targeting_res:
                        continue

                    if line_item_targeting_res['type'] == 'existing':
                        existing_count +=1
                    if line_item_targeting_res['type'] == 'new':
                        new_count +=1
                    sync_success += 1
                elif 'success' in line_item_targeting_res and line_item_targeting_res['success'] is False:
                    sync_fail += 1

            res['sync']['type'] = {}
            res['sync']['type']['existing'] = existing_count
            res['sync']['type']['new'] = new_count
            res['sync']['total'] = sync_success
            if sync_fail == 0:
                res['sync']['success'] = True
            else:
                res['sync']['success'] = False

        return res


    @classmethod
    def set_targeting(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['success'] = False

        account_id_int = account_id
        account_id_base36 = int_to_base36(account_id)

        if account_id_base36 is None:
            res = {
                'data': {},
                'success': False,
                'message': "Invaid Twitter Account ID"
            }
            return res

        # Sort input data by line_item_id
        data_sort_by_line_item = {}
        m_tw_line_item_targeting_list = []

        for item in data:
            data_sort_by_line_item.setdefault((item['tw_line_item_id']),[]).append(item)

        new_list    = []
        # Compare targeting list with what we have in the DB
        for line_item_targeting in data_sort_by_line_item.values():
            if line_item_targeting[0]['tw_line_item_id']:
                line_item_id = line_item_targeting[0]['tw_line_item_id']

            try:
                m_tw_line_item_targeting = TwitterTargeting.objects_raw.filter(tw_line_item_id=line_item_id).values()
            except TwitterTargeting.DoesNotExist:
                continue

            m_tw_line_item_targeting_list = list(m_tw_line_item_targeting)  # converts ValuesQuerySet into Python list



            for item in line_item_targeting:
                matching_item = False
                for m_item in m_tw_line_item_targeting_list:
                    if int(m_item['tw_targeting_type']) == int(item['tw_targeting_type']) and \
                       m_item['targeting_value'] == item['targeting_value'] and \
                       m_item['tw_targeting_id'] == item['tw_targeting_id']:
                        # Even if above condition is met, addition check is required for tailored
                        # audience for include and exclude
                        if m_item['tw_targeting_type'] == 18:
                            if not (item['targeting_params'] == m_item['targeting_params'] or \
                                # there are no targeting_params value for old tailored
                                # audiences(we support only EXCLUDED at that time)
                                'EXCLUDED' in item['targeting_params'] and not m_item['targeting_params']):
                                break

                        # Remove matching existing item from list
                        m_tw_line_item_targeting_list.remove(m_item)
                        matching_item = True
                        break

                if matching_item is False:
                    new_list.append(item)

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)

        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX

        delete_list = m_tw_line_item_targeting_list
        post_data = []

        for delete_item in delete_list:
            delete_item_data = {}
            params = self.format_params(delete_item, 'delete')
            if not params:
                continue
            delete_item_data['operation_type'] = 'Delete'
            delete_item_data['params'] = params

            # if type is PLATFORM_VERSION, deletion should be done without batch
            if params['targeting_type'] == 'PLATFORM_VERSION':
                res = TwitterTargeting.delete(delete_item, account_id)
            else:
                post_data.append(delete_item_data)

        for new_item in new_list:
            new_item_data = {}
            params = self.format_params(new_item)
            if not params:
                continue
            new_item_data['operation_type'] = 'Create'
            new_item_data['params'] = params
            post_data.append(new_item_data)

        if not post_data:
            res['data']    = []
            res['success'] = True
            res['message'] = "No new Line Item Targetings"
            return res

        # Split up requests into batches of 20
        batch = []
        batches = []
        for x in range(0, len(post_data), 20):
            batch = post_data[x:x+20]
            batches.append(batch)

        success_batch = []
        error_batch   = []
        error_details = []
        success       = False
        error         = False

        for batch_post in batches:
            try:
                account = client.accounts(account_id_base36)
                headers = {
                    "Content-Type": "application/json"
                }
                resource = '/{api_version}/batch/accounts/{account_id}/targeting_criteria'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
                response = Request(client, 'post', resource, body=json.dumps(batch_post), headers=headers).perform()
                if response.code == 200 or response.code == 201:
                    success = True
                    success_batch.extend(response.body['data'])

            except Error as e:
                error = True
                if e.response.body.get('operation_errors', None) is not None:
                    for err in e.response.body.get('operation_errors'):
                        if err:
                            if isinstance(err, dict):
                                err = [err]
                            error_details.extend(err)
                if e.response.body.get('errors', None) is not None:
                    for err in e.response.body.get('errors'):
                        if err:
                            if isinstance(err, dict):
                                err = [err]
                            error_details.extend(err)
                    error_details.extend(err)

                error_batch.extend(batch_post)

            except Exception as e:
                res = {
                    'data': [],
                    'success': False,
                    'message': str(e)
                }
                error_batch.extend(batch_post)

        if success_batch and success:
            res['sync'] = {}

            if isinstance(success_batch, dict):
                success_batch = [success_batch]

            sync_success   = 0
            sync_fail      = 0
            new_count      = 0
            existing_count = 0
            deleted_count  = 0

            for index, api_line_item_targeting in enumerate(success_batch, start=0):
                line_item_id_int = base36_to_int(api_line_item_targeting['line_item_id'])
                api_line_item_targeting['account_id'] = account_id
                line_item_targeting_res = self.sync_targeting(account_id_int, line_item_id_int, api_line_item_targeting)

                if 'success' in line_item_targeting_res and line_item_targeting_res['success'] is True:
                    if 'skip' in line_item_targeting_res:
                        continue

                    if line_item_targeting_res['type'] == 'existing':
                        existing_count +=1
                    if line_item_targeting_res['type'] == 'new':
                        new_count +=1
                    if line_item_targeting_res['type'] == 'delete':
                        deleted_count += 1
                    sync_success += 1
                elif 'success' in line_item_targeting_res and line_item_targeting_res['success'] is False:
                    sync_fail += 1

            res['sync']['type']             = {}
            res['sync']['type']['existing'] = existing_count
            res['sync']['type']['new']      = new_count
            res['sync']['type']['delete']   = deleted_count
            res['sync']['total']            = sync_success

            if sync_fail == 0:
                res['sync']['success'] = True
            else:
                res['sync']['success'] = False

        res['success']          = success
        res['count']            = {}
        res['count']['success'] = len(success_batch)
        res['count']['total']   = len(data)
        res['count']['error']   = len(error_batch)
        res['data']             = success_batch

        if error:
            res['success']           = False
            res['error']             = {}
            res['error']['data']     = error_batch
            res['error']['messages'] = filter(None, error_details)

        return res


    @classmethod
    def sync_targeting(self, tw_account_id, tw_line_item_id, data):
        res = {}
        res['data'] = data
        res['success'] = False
        criteria_id_int = base36_to_int(data['id'])

        if data.get('deleted'):
            TwitterTargeting.objects_raw.filter(tw_criteria_id=criteria_id_int).delete()
            return {'success': True, 'type': 'delete'}

        m_targeting_obj = None

        if isinstance(tw_line_item_id, TwitterLineItem):
            m_tw_line_item = tw_line_item_id
        else:
            m_tw_line_item = TwitterLineItem.objects_raw.filter(tw_line_item_id=tw_line_item_id).first()

        if m_tw_line_item is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Line Item Targeting. Cannot find Twitter Line Item"
            }
            return res

        if data['targeting_type'] in TW_TARGETING_TYPE:
            targeting_conf = TW_TARGETING_TYPE[data['targeting_type']]
            targeting_type = targeting_conf['type']
            targeting_type_value = targeting_conf['value']
            targeting_value = data['targeting_value']
            targeting_params = None

            if 'tailored_audience_type' in data:
                targeting_params = data['tailored_audience_type']

            if isinstance(targeting_value,(int,long)):
                targeting_value = targeting_value
            if isinstance(targeting_value, six.string_types):
                try:
                    if TW_TARGETING_VALUE_TYPE[targeting_type_value] == 'base36':
                        targeting_value = base36_to_int(targeting_value)
                except ValueError:
                    targeting_value = targeting_value

            if targeting_type == 'enum':
                # 1=, 2=location, 3=platform, 4=device, 5=, 6=,
                # 7=, 8=followers, 9=similar_followers, 10=broad_keyword, 11=unordered_keyword,
                # 12=phrase_keyword, 13=exact_keyword, 14=app_store_category, 15=network_operator, 16=os_version, 17=user_interest
                # 18=tailored_audience, 19=tv_genre, 20=tv_channel, 21=tv_shows, 22=behavior_expanded, 23=event, 24=behavior
                try:
                    if targeting_type_value == 2:
                        m_targeting_obj = TwitterLocation.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 4:
                        m_targeting_obj = TwitterDevice.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 14:
                        m_targeting_obj = TwitterAppCategory.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 15:
                        m_targeting_obj = TwitterCarrier.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 16:
                        m_targeting_obj = TwitterOsVersion.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 17:
                        m_targeting_obj = TwitterUserInterest.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 18:
                        m_targeting_obj = TwitterTailoredAudience.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 19:
                        m_targeting_obj = TwitterTVGenre.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 20:
                        m_targeting_obj = TwitterTVChannel.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 22 or targeting_type_value == 24:
                        m_targeting_obj = TwitterBehavior.objects_raw.filter(tw_targeting_id=targeting_value).first()

                    elif targeting_type_value == 23:
                        m_targeting_obj = TwitterEvent.objects_raw.filter(tw_targeting_id=targeting_value).first()
                        if not m_targeting_obj:
                            d = TwitterEvent.fetch_event_by_id(dict(account_id=data['account_id'],
                                                                    event_id=targeting_value))
                            if d.get('data') and len(d['data']) == 1:
                                d = d['data'][0]
                                m_targeting_obj = TwitterEvent(tw_targeting_id=targeting_value, name=d['name'],
                                                               start_time=d['start_time'], end_time=d['end_time'])
                                m_targeting_obj.save()
                except TwitterLocation.DoesNotExist:
                    m_targeting_obj = None
                except TwitterDevice.DoesNotExist:
                    m_targeting_obj = None
                except TwitterAppCategory.DoesNotExist:
                    m_targeting_obj = None
                except TwitterCarrier.DoesNotExist:
                    m_targeting_obj = None
                except TwitterOsVersion.DoesNotExist:
                    m_targeting_obj = None
                except TwitterUserInterest.DoesNotExist:
                    m_targeting_obj = None
                except TwitterTailoredAudience.DoesNotExist:
                    m_targeting_obj = None

                if m_targeting_obj is not None:

                    try:
                        res['type'] = 'existing'
                        m_tw_line_item_targeting = TwitterTargeting.objects_raw.get(tw_line_item_id=m_tw_line_item.pk, tw_criteria_id=criteria_id_int)
                    except TwitterTargeting.DoesNotExist:
                        res['type'] = 'new'
                        m_tw_line_item_targeting = TwitterTargeting(tw_line_item_id=m_tw_line_item.pk, tw_criteria_id=criteria_id_int)

                    if m_tw_line_item_targeting is None:
                        res = {
                            'data': {},
                            'success': False,
                            'message': "Error syncing Twitter Line Item Targeting"
                        }
                        return res
                    m_tw_line_item_targeting.tw_targeting_id = targeting_value
                    m_tw_line_item_targeting.name = data['name']
                    m_tw_line_item_targeting.tw_targeting_type = targeting_type_value
                    m_tw_line_item_targeting.targeting_params = targeting_params
                    m_tw_line_item_targeting.save_raw()
                    res['success'] = True

            elif targeting_type == 'string':
                try:
                    res['type'] = 'existing'
                    m_tw_line_item_targeting = TwitterTargeting.objects_raw.get(tw_line_item_id=m_tw_line_item.pk, tw_criteria_id=criteria_id_int, targeting_value=data['targeting_value'])
                except TwitterTargeting.DoesNotExist:
                    res['type'] = 'new'
                    m_tw_line_item_targeting = TwitterTargeting(tw_line_item_id=m_tw_line_item.pk, tw_criteria_id=criteria_id_int)

                if m_tw_line_item_targeting is None:
                    res = {
                        'data': {},
                        'success': False,
                        'message': "Error syncing Twitter Line Item Targeting"
                    }
                    return res

                m_tw_line_item_targeting.name = data['name']
                m_tw_line_item_targeting.tw_targeting_type = targeting_type_value
                m_tw_line_item_targeting.targeting_value = data['targeting_value']
                try:
                    m_tw_line_item_targeting.save_raw()
                    res['success'] = True
                except _mysql_exceptions.Warning, e:
                   res = {
                        'data': {},
                        'success': False,
                        'message': "Error syncing Twitter Line Item Targeting"
                    }
                return res
        else:
            res['success'] = True
            res['skip'] = True
        return res
