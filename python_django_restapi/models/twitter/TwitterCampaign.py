import re
import json
import restapi.audit_logger as audit
from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED, STATUS_ARCHIVED
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.fields import ZeroDateTimeField
from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error
from twitter_ads.utils import format_time


AUDIT_TYPE_TW_CAMPAIGN = 16

# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/campaigns

class TwitterCampaignManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterCampaignManager, self).own(queryset)
        return queryset


class TwitterCampaign(BaseModel):
    tw_campaign_id = models.BigIntegerField(primary_key=True)
    tw_account_id = models.ForeignKey(TwitterAccount, db_column='tw_account_id')
    campaign_id = models.ForeignKey(Campaign, db_column='campaign_id')
    name = models.CharField(max_length=255)
    funding_instrument_id = models.CharField(max_length=255)
    start_time = ZeroDateTimeField(default=None, null=True, blank=True)
    end_time = ZeroDateTimeField(default=None, null=True, blank=True)
    standard_delivery = models.NullBooleanField()
    frequency_cap = models.IntegerField()
    duration_in_days = models.CharField(max_length=8, choices=[(1,1), (7,7), (30,30)], default=7)
    total_budget_amount_local_micro = models.BigIntegerField(max_length=20)
    daily_budget_amount_local_micro = models.BigIntegerField(max_length=20)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterCampaignManager()
    objects_raw = models.Manager()
    # permission_check = True

    search_args = ('name__icontains', 'tw_campaign_id', )

    @property
    def search_result(self):
        advertiser = self.campaign_id.advertiser_id
        result = {'level': 'twittercampaign',
                  'campaign': self.campaign_id.campaign,
                  'campaign_id': self.campaign_id.campaign_id,
                  'tw_campaign': "%s / %s" % (self.tw_account_id.name, self.name),
                  'tw_campaign_id': self.tw_campaign_id,
                  'advertiser': advertiser.advertiser,
                  'advertiser_id': advertiser.advertiser_id,
                  'last_update': self.last_update}
        return result

    @property
    def _advertiser_id(self):
        return self.campaign_id.advertiser_id.advertiser_id

    @property
    def _campaign_id(self):
        return self.campaign_id.campaign_id

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_campaign'
        app_label = 'restapi'


    @classmethod
    def fetch_campaigns(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')
        campaign_id = data.get('campaign_id')
        tw_campaign_id = data.get('tw_campaign_id')

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id = int_to_base36(account_id)

        if isinstance(tw_campaign_id,(int,long)):
            tw_campaign_id_int = tw_campaign_id
            tw_campaign_id = int_to_base36(tw_campaign_id)

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
            # If Manage Campaign ID passed, fetch all Campaigns and find Manage Campaign
            if campaign_id:
                resource = '/{api_version}/accounts/{account_id}/campaigns?count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
                response = Request(client, 'get', resource).perform()

                if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                    send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

                for campaign in response.body['data']:
                    campaign_id_match = re.findall(r'\s*{(\d+)}\s*$', campaign['name'])[:1]
                    if campaign_id_match and campaign_id_match[0] and int(campaign_id_match[0]) == int(campaign_id):
                        res['data'].append(campaign)
                res['success'] = True
            else:
                if tw_campaign_id:
                    resource = '/{api_version}/accounts/{account_id}/campaigns/{tw_campaign_id}?count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, tw_campaign_id=tw_campaign_id)
                else:
                    resource = '/{api_version}/accounts/{account_id}/campaigns?count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id)

                response = Request(client, 'get', resource).perform()

                if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                    send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

                res['data'] = response.body['data']

                next_cursor = None
                if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                    next_cursor = response.body['next_cursor']
                    while next_cursor is not 0:
                        if tw_campaign_id:
                            resource = '/{api_version}/accounts/{account_id}/campaigns/{tw_campaign_id}?cursor={next_cursor}&count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, tw_campaign_id=tw_campaign_id, next_cursor=next_cursor)
                        else:
                            resource = '/{api_version}/accounts/{account_id}/campaigns?cursor={next_cursor}&count=1000&with_deleted=true'.format(api_version=settings.TW_API_VERSION, account_id=account.id, next_cursor=next_cursor)

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
                for index, api_campaign in enumerate(res['data'], start=0):
                    campaign_res = self.sync_campaign(account_id_int, api_campaign)
                    if 'success' in campaign_res and campaign_res['success'] is True:
                        if campaign_res['type'] == 'existing':
                            existing_count +=1
                        if campaign_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1

                    elif 'success' in campaign_res and campaign_res['success'] is False:
                        sync_fail += 1

                res['os_platform'] = campaign_res['os_platform']
                res['sync']['type'] = {}
                res['sync']['type']['existing'] = existing_count
                res['sync']['type']['new'] = new_count
                res['sync']['total'] = sync_success
                if sync_fail == 0:
                    res['sync']['success'] = True
                else:
                    res['sync']['success'] = False

            elif isinstance(res['data'], dict):
                campaign_res = self.sync_campaign(account_id_int, res['data'])

                if 'success' in campaign_res and campaign_res['success'] is True:
                    res['data'] = campaign_res['data']
                    res['os_platform'] = campaign_res['os_platform']
                    res['sync']['success'] = campaign_res['success']
                    res['sync']['type'] = {}
                    res['sync']['type'][campaign_res['type']] = 1
                    res['sync']['total'] = 1

                elif 'success' in campaign_res and campaign_res['success'] is False:
                    res['data'] = campaign_res['data']
                    res['sync']['success'] = campaign_res['success']
                    res['sync']['message'] = campaign_res['message']
        return res


    @classmethod
    def create_campaign(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_campaign(data, oauth_token, oauth_token_secret, "post")

    @classmethod
    def update_campaign(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_update_campaign(data, oauth_token, oauth_token_secret, "put")

    @classmethod
    def create(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.create_campaign(data, oauth_token, oauth_token_secret)

    @classmethod
    def update(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.update_campaign(data, oauth_token, oauth_token_secret)

    @classmethod
    def create_update_campaign(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET, request_type="post"):
        res = {}
        res['sync'] = {}
        res['success'] = False
        account_id = data.get('account_id')
        campaign_id = data.get('tw_campaign_id')

        if isinstance(campaign_id,(int,long)):
            campaign_id_int = campaign_id
            campaign_id = int_to_base36(campaign_id)

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

        if request_type == 'put':
            if campaign_id is None:
                res = {
                    'data': {},
                    'success': False,
                    'message': "Missing Twitter Campaign ID"
                }
                return res
        params = {}
        params['daily_budget_amount_local_micro'] = data.get('daily_budget_amount_local_micro', None)
        params['duration_in_days']                = data.get('duration_in_days', None)
        params['end_time']                        = data.get('end_time', None)
        params['frequency_cap']                   = data.get('frequency_cap', None)
        params['funding_instrument_id']           = data.get('funding_instrument_id', None)
        params['name']                            = data.get('name', None)
        if data.get('paused', None) is not None:
            params['paused']                      = 'true' if data.get('paused') else 'false'
        params['standard_delivery']               = str(data.get('standard_delivery')).lower() if data.get('standard_delivery') else None
        params['start_time']                      = data.get('start_time', None)
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
                resource = '/{api_version}/accounts/{account_id}/campaigns/{campaign_id}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, campaign_id=campaign_id)
            elif request_type == 'post':
                resource = '/{api_version}/accounts/{account_id}/campaigns'.format(api_version=settings.TW_API_VERSION, account_id=account.id)

            response = Request(client, request_type, resource, params=params).perform()

            if response.code == 200 or response.code == 201:
                res['success'] = True

            res['data'] = response.body['data']

            if res['data'] and res['success']:
                campaign_res = self.sync_campaign(account_id_int, res['data'])

                if 'success' in campaign_res and campaign_res['success'] is True:
                    res['data'] = campaign_res['data']
                    res['sync']['success'] = campaign_res['success']
                    res['sync']['type'] = {}
                    res['sync']['type'][campaign_res['type']] = 1
                    res['sync']['total'] = 1

                elif 'success' in campaign_res and campaign_res['success'] is False:
                    res['data'] = campaign_res['data']
                    res['sync']['success'] = campaign_res['success']
                    res['sync']['message'] = campaign_res['message']

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
        return self.batch_create_update_campaign(data, account_id, oauth_token, oauth_token_secret, "post")

    @classmethod
    def batch_update(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        return self.batch_create_update_campaign(data, account_id, oauth_token, oauth_token_secret, "put")

    @classmethod
    def batch_create_update_campaign(self, data, account_id, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET, request_type="post"):
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
            for campaign in data:
                campaign_data = {}
                params = {}
                params['daily_budget_amount_local_micro'] = campaign.get('daily_budget_amount_local_micro', None)
                params['duration_in_days']                = campaign.get('duration_in_days', None)
                params['end_time']                        = campaign.get('end_time', None)
                params['frequency_cap']                   = campaign.get('frequency_cap', None)
                params['funding_instrument_id']           = campaign.get('funding_instrument_id', None)
                params['name']                            = campaign.get('name', None)
                if campaign.get('paused', None) is not None:
                    params['paused']                      = 'true' if campaign.get('paused') else 'false'
                params['standard_delivery']               = str(campaign.get('standard_delivery')).lower() if campaign.get('standard_delivery') else None
                params['start_time']                      = campaign.get('start_time', None)
                params['total_budget_amount_local_micro'] = campaign.get('total_budget_amount_local_micro', None)

                # total_budget_amount_local_micro = 0 is not permitted
                if not params['total_budget_amount_local_micro']:
                    params['total_budget_amount_local_micro'] = None
                params = dict((k,v) for k,v in params.iteritems() if v is not None and v is not "")

                if request_type == 'post':
                    campaign_data['operation_type'] = 'Create'
                if request_type == 'put':
                    campaign_data['operation_type'] = 'Update'

                campaign_data['params'] = params
                post_data.append(campaign_data)

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
                    resource = '/{api_version}/batch/accounts/{account_id}/campaigns'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
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

                for index, api_campaign in enumerate(success_batch, start=0):
                    campaign_res = self.sync_campaign(account_id_int, api_campaign)
                    if 'success' in campaign_res and campaign_res['success'] is True:
                        if campaign_res['type'] == 'existing':
                            existing_count +=1
                        if campaign_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1

                    elif 'success' in campaign_res and campaign_res['success'] is False:
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
    def sync_campaign(self, tw_account_id, data, manage_campaign_id=None):
        res = {}
        res['data'] = data
        res['success'] = False
        res['os_platform'] = 'web'
        campaign_id_int = base36_to_int(data['id'])

        if isinstance(tw_account_id, TwitterAccount):
            m_tw_account = tw_account_id
        else:
            m_tw_account = TwitterAccount.objects_raw.get(tw_account_id=tw_account_id)

        if m_tw_account is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Campaign Cannot find Twitter Account"
            }
            return res

        try:
            res['type'] = 'existing'
            m_tw_campaign = TwitterCampaign.objects_raw.get(tw_account_id=m_tw_account, tw_campaign_id=campaign_id_int)
        except TwitterCampaign.DoesNotExist:
            res['type'] = 'new'
            m_tw_campaign = TwitterCampaign(tw_account_id=m_tw_account, tw_campaign_id=campaign_id_int)

        if m_tw_campaign is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Campaign"
            }
            return res

        # Get Manage Campaign ID from Twitter Campaign Name
        if manage_campaign_id is None:
            campaign_id_match = re.findall(r'\s*{(\d+)}\s*$', data['name'])[:1]
            if campaign_id_match and campaign_id_match[0]:
                manage_campaign_id = campaign_id_match[0]

        if manage_campaign_id:
            try:
                m_campaign = Campaign.objects_raw.get(campaign_id=manage_campaign_id)
            except Campaign.DoesNotExist:
                m_campaign = None

            if m_campaign is not None:
                m_tw_campaign.campaign_id = m_campaign
                res['data']['manage_campaign_id'] = manage_campaign_id
                if m_campaign.targeting:
                    targeting = json.loads(m_campaign.targeting);
                    if targeting and 'os' in targeting and targeting['os']:
                        os_platform = targeting['os']
                        if os_platform == 'iOS':
                            os_platform = 'iphone'
                        res['os_platform'] = os_platform

                m_tw_campaign.name                            = data['name']
                m_tw_campaign.funding_instrument_id           = data['funding_instrument_id']
                m_tw_campaign.total_budget_amount_local_micro = data['total_budget_amount_local_micro']
                m_tw_campaign.daily_budget_amount_local_micro = data['daily_budget_amount_local_micro']
                m_tw_campaign.duration_in_days                = data['duration_in_days']
                m_tw_campaign.standard_delivery               = data['standard_delivery']

                if data['start_time'] is not None:
                    m_tw_campaign.start_time = data['start_time']
                if data['end_time'] is not None:
                    m_tw_campaign.end_time = data['end_time']
                if data['paused'] == True or data['servable'] is False:
                    m_tw_campaign.status = STATUS_PAUSED
                elif data['paused'] == False or data['servable'] is True:
                    m_tw_campaign.status = STATUS_ENABLED
                if data['deleted'] == True:
                    m_tw_campaign.status = STATUS_ARCHIVED
                if data['duration_in_days'] is not None:
                    m_tw_campaign.duration_in_days = data['duration_in_days']
                if data['frequency_cap'] is not None:
                    m_tw_campaign.frequency_cap = data['frequency_cap']

                m_tw_campaign.save_raw()
                res['success'] = True
        else:
            res['success'] = False
            res['message'] = 'Missing Manage Campaign ID'

        return res

audit.AuditLogger.register(TwitterCampaign, audit_type=AUDIT_TYPE_TW_CAMPAIGN, check_delete='physical_delete')
