import json
import restapi.audit_logger as audit

from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.choices import STATUS_CHOICES, STATUS_ARCHIVED, STATUS_PAUSED, STATUS_ENABLED, TW_PRODUCT_TYPES, TW_PLACEMENTS, TW_OBJECTIVES, TW_BID_TYPES, TW_BID_UNITS, TW_OPTIMIZATIONS, TW_CHARGE_BYS
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.registry import REGISTRY

from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error
from twitter_ads.utils import format_time


AUDIT_TYPE_TW_LINE_ITEM = 17

# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/line_items

class TwitterLineItemManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterLineItemManager, self).own(queryset)
        #queryset = queryset.filter(tw_campaign_id__campaign_id__advertiser_id__agency_id__trading_desk_id_id__in=REGISTRY['user_trading_desk_ids'])
        return queryset


class TwitterLineItem(BaseModel):
    tw_line_item_id = models.BigIntegerField(primary_key=True)
    tw_campaign_id = models.ForeignKey(TwitterCampaign, db_column='tw_campaign_id')
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=255, default='USD')
    start_time = DateTimeField()
    end_time = DateTimeField()
    product_type = models.CharField(max_length=40, choices=TW_PRODUCT_TYPES, default='PROMOTED_TWEETS')
    placements = models.TextField(blank=True)
    primary_web_event_tag = models.CharField(max_length=255)
    objective = models.CharField(max_length=40, choices=TW_OBJECTIVES, default='APP_INSTALLS')

    bid_amount_local_micro = models.BigIntegerField(max_length=20)
    bid_amount_computed_reason = models.TextField(default='')
    bid_amount_computed = models.BigIntegerField(max_length=20)
    bid_override = models.NullBooleanField()

    bid_type = models.CharField(max_length=40, choices=TW_BID_TYPES, default='AUTO')
    bid_unit = models.CharField(max_length=40, choices=TW_BID_UNITS, default='APP_INSTALL')
    optimization = models.CharField(max_length=40, choices=TW_OPTIMIZATIONS, default='APP_INSTALL')
    charge_by = models.CharField(max_length=40, choices=TW_CHARGE_BYS, default='APP_INSTALL')
    categories = models.TextField(blank=True)
    tracking_tags = models.TextField(blank=True)
    automatically_select_bid = models.NullBooleanField()
    total_budget_amount_local_micro = models.BigIntegerField(max_length=20)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterLineItemManager()
    objects_raw = models.Manager()
    # permission_check = True

    search_args = ('name__icontains', 'tw_line_item_id', )
    
    @property
    def search_result(self):
        tw_campaign = self.tw_campaign_id
        campaign = tw_campaign.campaign_id
        advertiser = campaign.advertiser_id
        result = {'level': 'twitterlineitem',
                  'campaign': campaign.campaign,
                  'campaign_id': campaign.campaign_id,
                  'tw_campaign': tw_campaign.name,
                  'tw_campaign_id': tw_campaign.tw_campaign_id,
                  'tw_line_item': "%s / %s" % (campaign.campaign, self.name),
                  'tw_line_item_id': self.tw_line_item_id,
                  'advertiser': advertiser.advertiser,
                  'advertiser_id': advertiser.advertiser_id,
                  'last_update': self.last_update}
        return result

    @property
    def _advertiser_id(self):
        return self.tw_campaign_id.campaign_id.advertiser_id.advertiser_id

    @property
    def _campaign_id(self):
        return self.tw_campaign_id.campaign_id.campaign_id

    @property
    def _tw_campaign_id(self):
        return self.tw_campaign_id.tw_campaign_id

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_line_item'
        app_label = 'restapi'

    def is_own(self):
        return bool(self.campaign_id.advertiser_id.agency_id.trading_desk_id.trading_desk_userprofiles
                    .filter(user=REGISTRY['user']))


    @classmethod
    def fetch_line_items(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')
        campaign_id = data.get('campaign_id')
        line_item_id = data.get('line_item_id')
        campaign_id_int = None

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id = int_to_base36(account_id)

        if isinstance(campaign_id,(int,long)):
            campaign_id_int = campaign_id
            campaign_id = int_to_base36(campaign_id)

        if isinstance(line_item_id,(int,long)):
            line_item_id = int_to_base36(line_item_id)

        if account_id is None:
            res = {
                'data': {},
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
            resource = '/{api_version}/accounts/{account_id}/line_items?with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
            if campaign_id is not None:
                resource = '/{api_version}/accounts/{account_id}/line_items?campaign_ids={campaign_id}&count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, campaign_id=campaign_id)

            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            res['data'] = response.body['data']

            next_cursor = None
            if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                next_cursor = response.body['next_cursor']
                while next_cursor is not 0:
                    resource = '/{api_version}/accounts/{account_id}/line_items?cursor={next_cursor}&count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, next_cursor=next_cursor)
                    if campaign_id is not None:
                        resource = '/{api_version}/accounts/{account_id}/line_items?campaign_ids={campaign_id}&count=1000&cursor={next_cursor}&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, campaign_id=campaign_id, next_cursor=next_cursor)

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
                for index, api_line_item in enumerate(res['data'], start=0):
                    if campaign_id_int is None:
                        campaign_id_int = base36_to_int(api_line_item['campaign_id'])

                    line_item_res = self.sync_line_item(account_id_int, campaign_id_int, api_line_item)
                    if 'success' in line_item_res and line_item_res['success'] is True:
                        if line_item_res['type'] == 'existing':
                            existing_count +=1
                        if line_item_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1

                    elif 'success' in line_item_res and line_item_res['success'] is False:
                        sync_fail += 1
                res['sync']['type'] = {}
                res['sync']['type']['existing'] = existing_count
                res['sync']['type']['new'] = new_count
                res['sync']['total'] = sync_success
                if sync_fail == 0:
                    res['sync']['success'] = True
                else:
                    res['sync']['success'] = False

            elif isinstance(res['data'], dict):
                line_item_res = self.sync_line_item(account_id_int, campaign_id_int, res['data'])

                if 'success' in line_item_res and line_item_res['success'] is True:
                    res['data'] = line_item_res['data']
                    res['sync']['success'] = line_item_res['success']
                    res['sync']['type'] = {}
                    res['sync']['total'] = 1
                    res['sync']['type'][line_item_res['type']] = 1

                elif 'success' in line_item_res and line_item_res['success'] is False:
                    res['data'] = line_item_res['data']
                    res['sync']['success'] = line_item_res['success']
                    res['sync']['message'] = line_item_res['message']
        return res


    @classmethod
    def get_line_item(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        account_id = data.get('account_id')
        line_item_id = data.get('line_item_id')

        if isinstance(line_item_id,(int,long)):
            line_item_id = int_to_base36(line_item_id)

        if isinstance(account_id,(int,long)):
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

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            account = client.accounts(account_id)
            resource = '/{api_version}/accounts/{account_id}/line_items/{line_item_id}?count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, line_item_id=line_item_id)
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
                'data': {},
                'success': False,
                'message': str(e)
            }
        return res

    @classmethod
    def create(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_line_item(data, oauth_token, oauth_token_secret, "post")

    @classmethod
    def update(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_line_item(data, oauth_token, oauth_token_secret, "put")

    @classmethod
    def create_update_line_item(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET, request_type="post"):
        res             = {}
        res['sync']     = {}
        account_id      = data.get('account_id', None)
        campaign_id     = data.get('campaign_id', None)
        line_item_id    = data.get('line_item_id', None)
        campaign_id_int = None

        if isinstance(campaign_id,(int,long)):
            campaign_id_int = campaign_id
            campaign_id = int_to_base36(campaign_id)
            data['campaign_id'] = campaign_id

        if isinstance(line_item_id,(int,long)):
            line_item_id_int = line_item_id
            line_item_id = int_to_base36(line_item_id)

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id = int_to_base36(account_id)

        if account_id is None:
            res = {
                'data': [],
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        if request_type == 'post':
            if campaign_id is None:
                res = {
                    'data': [],
                    'success': False,
                    'message': "Missing Twitter Campaign ID"
                }
                return res

        if request_type == 'put':
            if line_item_id is None:
                res = {
                    'data': [],
                    'success': False,
                    'message': "Missing Twitter Line Item ID"
                }
                return res

        params = {}
        params['advertiser_domain']        = data.get('advertiser_domain', None)
        # automatically_set_bid and bid_type cannot be set in the same request
        # See https://dev.twitter.com/ads/reference/post/accounts/%3Aaccount_id/line_items#api-param-line-item-bid_type
        if data.get('automatically_select_bid', False) is True:
            params['automatically_select_bid'] = str(True).lower()
        else:
            params['bid_type']                 = data.get('bid_type', None)
            params['bid_amount_local_micro']   = data.get('bid_amount_local_micro', None)

        params['bid_amount_local_micro']   = data.get('bid_amount_local_micro', None)
        params['bid_type']                 = data.get('bid_type', None)
        params['bid_unit']                 = data.get('bid_unit', None)
        params['campaign_id']              = data.get('campaign_id', None)
        params['categories']               = data.get('categories', None)
        params['charge_by']                = data.get('charge_by', None)
        params['end_time']                 = data.get('end_time', None)
        params['include_sentiment']        = data.get('include_sentiment', 'POSITIVE_ONLY')
        params['name']                     = data.get('name', None)
        params['objective']                = data.get('objective', 'APP_INSTALLS')
        params['optimization']             = data.get('optimization', None)
        if data.get('paused', None) is not None:
            params['paused']               = 'true' if data.get('paused') else 'false'
        params['placements']               = data.get('placements', 'ALL_ON_TWITTER')
        params['product_type']             = data.get('product_type', 'PROMOTED_TWEETS')
        params['start_time']               = data.get('start_time', None)
        params['total_budget_amount_local_micro'] = data.get('total_budget_amount_local_micro', None)

        # total_budget_amount_local_micro = 0 is not permitted
        if not params['total_budget_amount_local_micro']:
            params['total_budget_amount_local_micro'] = None

        params = dict((k,v) for k,v in params.iteritems() if v is not None and v is not "")

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                            oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX

        try:
            account = client.accounts(account_id)

            if request_type == 'put':
                resource = '/{api_version}/accounts/{account_id}/line_items/{line_item_id}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, line_item_id=line_item_id)

            elif request_type == 'post':
                resource = '/{api_version}/accounts/{account_id}/line_items'.format(api_version=settings.TW_API_VERSION, account_id=account.id)

            response = Request(client, request_type, resource, params=params).perform()

            if response.code == 200 or response.code == 201:
                res['success'] = True

            res['data'] = response.body['data']

            if res['data'] and res['success']:
                if campaign_id_int is None and res['data']['campaign_id']:
                    campaign_id_int = base36_to_int(res['data']['campaign_id'])

                line_item_res = self.sync_line_item(account_id_int, campaign_id_int, res['data'])

                if 'success' in line_item_res and line_item_res['success'] is True:
                    res['data'] = line_item_res['data']
                    res['sync']['success'] = line_item_res['success']
                    res['sync']['type'] = {}
                    res['sync']['total'] = 1
                    res['sync']['type'][line_item_res['type']] = 1

                elif 'success' in line_item_res and line_item_res['success'] is False:
                    res['data'] = line_item_res['data']
                    res['sync']['success'] = line_item_res['success']
                    res['sync']['message'] = line_item_res['message']

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
    def batch_create(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.batch_create_update_line_item(data, account_id, oauth_token, oauth_token_secret, "post")

    @classmethod
    def batch_update(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.batch_create_update_line_item(data, account_id, oauth_token, oauth_token_secret, "put")

    @classmethod
    def batch_create_update_line_item(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET, request_type="post"):
        res             = {}
        res['success']  = False
        campaign_id_int = None

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id     = int_to_base36(account_id)

        if account_id is None:
            res = {
                'data': [],
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        if isinstance(data, (list, tuple)):
            post_data = []
            for line_item in data:
                line_item_data = {}
                params = {}
                params['bid_amount_local_micro']   = line_item.get('bid_amount_local_micro', None)
                params['bid_type']                 = line_item.get('bid_type', None)
                params['bid_unit']                 = line_item.get('bid_unit', None)
                params['campaign_id']              = line_item.get('campaign_id', None)
                params['categories']               = line_item.get('categories', None)
                params['charge_by']                = line_item.get('charge_by', None)
                params['end_time']                 = line_item.get('end_time', None)
                params['include_sentiment']        = line_item.get('include_sentiment', None)
                params['line_item_id']             = line_item.get('line_item_id', None)
                params['name']                     = line_item.get('name', None)
                params['objective']                = line_item.get('objective', 'APP_INSTALLS')
                params['primary_web_event_tag']    = line_item.get('primary_web_event_tag', None)
                params['optimization']             = line_item.get('optimization', None)
                params['paused']                   = str(line_item.get('paused')).lower() if line_item.get('paused') else None
                params['placements']               = line_item.get('placements', 'ALL_ON_TWITTER')
                params['product_type']             = line_item.get('product_type', 'PROMOTED_TWEETS')
                params['start_time']               = line_item.get('start_time', None)
                params['total_budget_amount_local_micro'] = line_item.get('total_budget_amount_local_micro', None)

                # total_budget_amount_local_micro = 0 is not permitted
                if not params['total_budget_amount_local_micro']:
                    params['total_budget_amount_local_micro'] = None

                params = dict((k,v) for k,v in params.iteritems() if v is not None and v is not "")

                if request_type == 'post':
                    line_item_data['operation_type'] = 'Create'
                if request_type == 'put':
                    line_item_data['operation_type'] = 'Update'
                line_item_data['params'] = params
                post_data.append(line_item_data)

            client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                    oauth_token_secret)

            if settings.TW_SANDBOX:
                client.sandbox = settings.TW_SANDBOX

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
                    account = client.accounts(account_id)
                    headers = {
                        "Content-Type": "application/json"
                    }
                    resource = '/{api_version}/batch/accounts/{account_id}/line_items'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
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

                for index, api_line_item in enumerate(success_batch, start=0):
                    #campaign_id could be different in line item bach
                    campaign_id_int = base36_to_int(api_line_item['campaign_id'])
                    line_item_res = self.sync_line_item(account_id_int, campaign_id_int, api_line_item)
                    if 'success' in line_item_res and line_item_res['success'] is True:
                        if line_item_res['type'] == 'existing':
                            existing_count +=1
                        if line_item_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1

                    elif 'success' in line_item_res and line_item_res['success'] is False:
                        sync_fail += 1

                res['sync']['type']             = {}
                res['sync']['type']['existing'] = existing_count
                res['sync']['type']['new']      = new_count
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

        elif isinstance(data, dict):
            if request_type == 'post':
                return self.create(data, oauth_token, oauth_token_secret)
            if request_type == 'put':
                return self.update(data, oauth_token, oauth_token_secret)


    @classmethod
    def sync_line_item(self, tw_account_id, tw_campaign_id, data):
        res = {}
        res['data'] = data
        res['success'] = False
        line_item_id_int = base36_to_int(data['id'])
        m_tw_campaign = None
        if isinstance(tw_campaign_id, TwitterCampaign):
            m_tw_campaign = tw_campaign_id
        else:
            try:
                m_tw_campaign = TwitterCampaign.objects_raw.get(tw_campaign_id=tw_campaign_id)
            except TwitterCampaign.DoesNotExist:
                m_tw_campaign = None

        if m_tw_campaign is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Line Item. Cannot find Twitter Campaign"
            }
            return res

        try:
            res['type'] = 'existing'
            m_tw_line_item = TwitterLineItem.objects_raw.get(tw_campaign_id=m_tw_campaign, tw_line_item_id=line_item_id_int)
        except TwitterLineItem.DoesNotExist:
            res['type'] = 'new'
            m_tw_line_item = TwitterLineItem(tw_campaign_id=m_tw_campaign, tw_line_item_id=line_item_id_int)
            m_tw_line_item.bid_amount_computed = data['bid_amount_local_micro']

        if m_tw_line_item is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Line Item"
            }
            return res

        m_tw_line_item.name                            = data['name']
        m_tw_line_item.product_type                    = data['product_type']
        m_tw_line_item.objective                       = data['objective']
        m_tw_line_item.placements                      = json.dumps(data['placements'])
        m_tw_line_item.primary_web_event_tag           = data['primary_web_event_tag']
        m_tw_line_item.bid_amount_local_micro          = data['bid_amount_local_micro']
        m_tw_line_item.bid_type                        = data['bid_type']
        m_tw_line_item.bid_unit                        = data['bid_unit']
        m_tw_line_item.optimization                    = data['optimization']
        m_tw_line_item.charge_by                       = data['charge_by']
        m_tw_line_item.categories                      = json.dumps(data['categories'])
        m_tw_line_item.automatically_select_bid        = data['automatically_select_bid']
        m_tw_line_item.total_budget_amount_local_micro = data['total_budget_amount_local_micro']
        m_tw_line_item.tracking_tags                   = json.dumps(data['tracking_tags'])

        if data['start_time'] is not None:
            m_tw_line_item.start_time = data['start_time']
        if data['end_time'] is not None:
            m_tw_line_item.end_time = data['end_time']
        if data['paused'] == True:
            m_tw_line_item.status = STATUS_PAUSED
        elif data['paused'] == False:
            m_tw_line_item.status = STATUS_ENABLED
        if data['deleted'] == True:
            m_tw_line_item.status = STATUS_ARCHIVED

        m_tw_line_item.save_raw()
        res['success'] = True

        return res

audit.AuditLogger.register(TwitterLineItem, audit_type=AUDIT_TYPE_TW_LINE_ITEM, check_delete='physical_delete')
