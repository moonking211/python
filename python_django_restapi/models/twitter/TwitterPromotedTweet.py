import json

import six

from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED, STATUS_ARCHIVED
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterAppCard import TwitterAppCard

from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error

# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/campaigns

class TwitterPromotedTweetManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterPromotedTweetManager, self).own(queryset)
        return queryset


class TwitterPromotedTweet(BaseModel):
    tw_promoted_tweet_id = models.BigIntegerField(primary_key=True)
    tw_line_item_id = models.ForeignKey(TwitterLineItem, db_column='tw_line_item_id')
    tw_tweet_id = models.BigIntegerField()
    tw_app_card_id = models.BigIntegerField()

    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterPromotedTweetManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_promoted_tweet'
        app_label = 'restapi'

    @property
    def _advertiser_id(self):
        return self.tw_line_item_id.tw_campaign_id.campaign_id.advertiser_id.advertiser_id

    @property
    def _campaign_id(self):
        return self.tw_line_item_id.tw_campaign_id.campaign_id.campaign_id

    @property
    def _tw_campaign_id(self):
        return self.tw_line_item_id.tw_campaign_id.tw_campaign_id

    @property
    def _tw_line_item_id(self):
        return self.tw_line_item_id.tw_line_item_id

    @classmethod
    def fetch_promoted_tweet(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        error_codes = {}
        account_id = data.get('account_id')
        line_item_id = data.get('line_item_id')
        os_platform = data.get('os_platform')
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
            resource = '/{api_version}/accounts/{account_id}/promoted_tweets?line_item_id={line_item_id}&count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id,line_item_id=line_item_id)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']

            next_cursor = None
            if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                next_cursor = response.body['next_cursor']
                while next_cursor is not 0:
                    resource = '/{api_version}/accounts/{account_id}/promoted_tweets?line_item_id={line_item_id}&count=1000&cursor={next_cursor}&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, line_item_id=line_item_id, next_cursor=next_cursor)
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
                'data': {},
                'success': False,
                'message': str(e)
            }

        if syncData and res['data'] and res['success']:
            res['sync'] = {}
            if isinstance(res['data'], (list, tuple)):
                sync_success = 0
                sync_fail = 0
                new_count = 0
                existing_count = 0
                for index, api_line_item_promoted_tweet in enumerate(res['data'], start=0):

                    line_item_promoted_tweet_res = self.sync_promoted_tweet(account_id_int, line_item_id_int, api_line_item_promoted_tweet, os_platform)
                    if 'success' in line_item_promoted_tweet_res and line_item_promoted_tweet_res['success'] is True:
                        if line_item_promoted_tweet_res['type'] == 'existing':
                            existing_count +=1
                        if line_item_promoted_tweet_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1
                    elif 'success' in line_item_promoted_tweet_res and line_item_promoted_tweet_res['success'] is False:
                        sync_fail += 1
                        if line_item_promoted_tweet_res.get('errors', None):
                            error_codes.update(line_item_promoted_tweet_res['errors'])

                res['sync']['type'] = {}
                res['sync']['type']['existing'] = existing_count
                res['sync']['type']['new'] = new_count
                res['sync']['total'] = sync_success
                if sync_fail == 0:
                    res['sync']['success'] = True
                else:
                    res['sync']['success'] = False
                    res['errors'] = error_codes

            elif isinstance(res['data'], dict):
                line_item_promoted_tweet_res = self.sync_promoted_tweet(account_id_int, line_item_id_int, res['data'])
                if 'success' in line_item_promoted_tweet_res and line_item_promoted_tweet_res['success'] is True:
                    res['data'] = line_item_promoted_tweet_res['data']
                    res['sync']['success'] = line_item_promoted_tweet_res['success']
                    res['sync']['type'] = {}
                    res['sync']['total'] = 1
                    res['sync']['type'][line_item_promoted_tweet_res['type']] = 1

                elif 'success' in line_item_promoted_tweet_res and line_item_promoted_tweet_res['success'] is False:
                    res['data'] = line_item_promoted_tweet_res['data']
                    res['sync']['success'] = line_item_promoted_tweet_res['success']
                    res['sync']['message'] = line_item_promoted_tweet_res['message']
                    if line_item_promoted_tweet_res.get('errors', None):
                        error_codes.update(line_item_promoted_tweet_res['errors'])
                    res['errors'] = error_codes

        return res

    @classmethod
    def set_promoted_tweet(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res               = {}
        res['success']    = True
        line_item_id      = data.get('line_item_id', None)
        tweet_ids         = data.get('tweet_ids', None)

        line_item_id_int     = line_item_id
        line_item_id_base_36 = int_to_base36(line_item_id)
        account_id_int       = int(account_id)
        account_id_base36    = int_to_base36(account_id)

        if account_id_base36 is None:
            res = {
                'data': {},
                'success': False,
                'message': "Invaid Twitter Account ID"
            }
            return res

        tweet_ids_list = map(lambda s:s.strip(), tweet_ids.split(','))

        try:
            m_tw_line_item_promoted_tweet = TwitterPromotedTweet.objects_raw.filter(tw_line_item_id=line_item_id).exclude(status=STATUS_ARCHIVED).values()
        except TwitterPromotedTweet.DoesNotExist:
            m_tw_line_item_promoted_tweet = None

        m_tw_line_item_promoted_tweet_list = list(m_tw_line_item_promoted_tweet)  # converts ValuesQuerySet into Python list

        new_list    = []

        for item in tweet_ids_list:
            matching_item = False
            for m_item in m_tw_line_item_promoted_tweet_list:
                if int(item) == int(m_item['tw_tweet_id']):
                    # Remove matching existing item from list
                    m_tw_line_item_promoted_tweet_list.remove(m_item)
                    matching_item = True
                    break

            if matching_item is False:
                new_list.append(item)

        delete_list = m_tw_line_item_promoted_tweet_list
        new_res = None
        delete_res = None

        if new_list:
            data_post = {
                "account_id"   : account_id_int,
                "line_item_id" : line_item_id_int,
                "tweet_ids"    :  ",".join(new_list),
            }
            new_res = self.create(data_post, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET)

        if delete_list:
            for item in delete_list:
                data_post = {
                    "account_id"   : account_id_int,
                    "line_item_id" : line_item_id_int,
                    "promoted_tweet_id": int_to_base36(item['tw_promoted_tweet_id']),
                }
                delete_res = self.delete(data_post, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET)

        if new_res:
            if new_res['success'] is False:
                res['success'] = False

        if delete_res:
            if delete_res['success'] is False:
                res['success'] = False

        # res['data'] = new_res['data']
        # res['sync'] = new_res['sync']
        return res

    @classmethod
    def create(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_promoted_tweet(data, oauth_token, oauth_token_secret, "post")

    @classmethod
    def update(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_promoted_tweet(data, oauth_token, oauth_token_secret, "put")

    @classmethod
    def delete(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_promoted_tweet(data, oauth_token, oauth_token_secret, "delete")

    @classmethod
    def create_update_promoted_tweet(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET, request_type="post"):
        res                = {}
        res['sync']        = {}
        account_id         = data.get('account_id', None)
        line_item_id       = data.get('line_item_id', None)
        tweet_ids          = data.get('tweet_ids', None)
        promoted_tweet_id  = data.get('promoted_tweet_id', None)
        line_item_id_int   = None

        line_item_id_int     = line_item_id
        line_item_id_base_36 = int_to_base36(line_item_id)
        account_id_int       = account_id
        account_id_base36    = int_to_base36(account_id)

        if account_id is None:
            res = {
                'data': {},
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        if request_type == 'put' or request_type == 'delete':
            if promoted_tweet_id is None:
                res = {
                    'data': {},
                    'success': False,
                    'message': "Missing Twitter Promoted Tweet ID"
                }
                return res

        if request_type == 'post':
            if tweet_ids is None:
                res = {
                    'data': {},
                    'success': False,
                    'message': "Missing Twitter Tweet IDs"
                }
                return res

            if line_item_id is None:
                res = {
                    'data': {},
                    'success': False,
                    'message': "Missing Twitter Line Item ID"
                }
                return res

        params = {}
        params['display_properties'] = data.get('display_properties', None)
        params['tweet_ids']          = data.get('tweet_ids', None)
        params['line_item_id']       = line_item_id_base_36
        params = dict((k,v) for k,v in params.iteritems() if v is not None and v is not "")
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                            oauth_token_secret)

        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX

        try:
            account = client.accounts(account_id_base36)

            if request_type == 'put' or request_type == 'delete':
                resource = '/{api_version}/accounts/{account_id}/promoted_tweets/{promoted_tweet_id}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, promoted_tweet_id=promoted_tweet_id)

            elif request_type == 'post':
                resource = '/{api_version}/accounts/{account_id}/promoted_tweets'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
            response = Request(client, request_type, resource, params=params).perform()
            if response.code == 200 or response.code == 201:
                res['success'] = True

            res['data'] = response.body['data']

            if res['data'] and res['success']:

                sync_success   = 0
                sync_fail      = 0
                new_count      = 0
                existing_count = 0
                deleted_count  = 0
                if request_type == 'delete':
                    res['data'] = [res['data']]
                for index, api_line_item_promoted_tweet in enumerate(res['data'], start=0):
                    line_item_id_int = base36_to_int(api_line_item_promoted_tweet['line_item_id'])
                    api_line_item_promoted_tweet['account_id'] = account_id

                    line_item_promoted_tweet_res = self.sync_promoted_tweet(account_id_int, line_item_id_int, api_line_item_promoted_tweet)

                    if 'success' in line_item_promoted_tweet_res and line_item_promoted_tweet_res['success'] is True:
                        if 'skip' in line_item_promoted_tweet_res:
                            continue

                        if line_item_promoted_tweet_res['type'] == 'existing':
                            existing_count +=1
                        if line_item_promoted_tweet_res['type'] == 'new':
                            new_count +=1
                        if line_item_promoted_tweet_res['type'] == 'delete':
                            deleted_count += 1
                        sync_success += 1
                    elif 'success' in line_item_promoted_tweet_res and line_item_promoted_tweet_res['success'] is False:
                        sync_fail += 1

                res['sync']['success'] = sync_fail == 0
                res['sync']['type'] = {}
                res['sync']['type']['existing'] = existing_count
                res['sync']['type']['new']      = new_count
                res['sync']['type']['delete']   = deleted_count

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

        return res

    @classmethod
    def sync_promoted_tweet(self, tw_account_id, tw_line_item_id, data, os_platform=None):
        from restapi.models.twitter.TwitterTweet import TwitterTweet
        res = {}
        res['data'] = data
        res['success'] = True
        promoted_tweet_id_int = base36_to_int(data['id'])
        m_tw_line_item_promoted_tweet = None

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

        if 'os_platform' not in data:
            os_platform = 'web'
            manage_campaign = m_tw_line_item.tw_campaign_id.campaign_id
            if manage_campaign and manage_campaign.targeting:
                targeting = json.loads(manage_campaign.targeting);
                if targeting and 'os' in targeting:
                    os_platform = targeting['os']
                    if os_platform == 'iOS':
                        os_platform = 'iphone'

        try:
            res['type'] = 'existing'
            m_tw_line_item_promoted_tweet = TwitterPromotedTweet.objects_raw.get(tw_line_item_id=m_tw_line_item, tw_promoted_tweet_id=promoted_tweet_id_int)
        except TwitterPromotedTweet.DoesNotExist:
            res['type'] = 'new'
            m_tw_line_item_promoted_tweet = TwitterPromotedTweet(tw_line_item_id=m_tw_line_item, tw_promoted_tweet_id=promoted_tweet_id_int)

        sync_tweet = True
        if m_tw_line_item_promoted_tweet.tw_app_card_id is not None:
            sync_tweet = False

        if m_tw_line_item_promoted_tweet is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Line Item Promoted Tweet. Cannot find Twitter Promoted Tweet"
            }
            return res

        if data['paused'] == True:
            m_tw_line_item_promoted_tweet.status = STATUS_PAUSED
        elif data['paused'] == False:
            m_tw_line_item_promoted_tweet.status = STATUS_ENABLED
        if data['deleted'] == True:
            res['type'] = 'delete'
            m_tw_line_item_promoted_tweet.status = STATUS_ARCHIVED
        m_tw_line_item_promoted_tweet.save()

        m_tw_line_item_promoted_tweet.tw_tweet_id = data['tweet_id']

        try:
            m_tw_line_item_tweet = TwitterTweet.objects_raw.get(tw_tweet_id=data['tweet_id'])
            sync_tweet = False
        except TwitterTweet.DoesNotExist:
            m_tw_line_item_tweet = TwitterTweet(tw_tweet_id=data['tweet_id'])

        if m_tw_line_item_tweet is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Line Item Tweet. Cannot find Twitter Tweet"
            }
            return res

        # Don't fetch tweet data if we already have tw_promoted_tweet.tw_app_card_id and tw_tweet.tw_tweet_id
        # https://managewiki.atlassian.net/browse/ADP-138
        if sync_tweet:
            api_tweet_details_data = TwitterTweet.fetch_tweet(dict(account_id=tw_account_id, tweet_id=data['tweet_id']))
            if api_tweet_details_data['success'] is False:
                res['success'] = False
                res['message'] = api_tweet_details_data['message'] if 'message' in api_tweet_details_data else ''
                res['errors'] = api_tweet_details_data['errors'] if 'errors' in api_tweet_details_data else {}

            # Check if App Card in Tweeet
            api_tweet_app_card = api_tweet_details_data.get('card_url')
            tweet_app_card = None
            if api_tweet_app_card is not None:
                try:
                    tweet_app_card = TwitterAppCard.objects_raw.get(preview_url=api_tweet_app_card)
                except TwitterAppCard.DoesNotExist:
                    tweet_app_card = None

                if tweet_app_card:
                    m_tw_line_item_promoted_tweet.tw_app_card_id = tweet_app_card.tw_app_card_id

            if m_tw_line_item_tweet:
                api_tweet_details = api_tweet_details_data['data']
                for api_tweet_detail in api_tweet_details:
                    if api_tweet_detail['platform'] == os_platform.lower():
                        m_tw_line_item_tweet.text = api_tweet_detail['preview']
                        m_tw_line_item_tweet.save_raw()
                        continue
        try:
            m_tw_line_item_promoted_tweet.save_raw()
            res['success'] = True
        except _mysql_exceptions.Warning, e:
           res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Line Item Targeting"
            }

        return res

