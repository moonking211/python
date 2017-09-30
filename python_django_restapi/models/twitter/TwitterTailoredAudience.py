import json
import restapi.audit_logger as audit
from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED, STATUS_ARCHIVED
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.twitter.TwitterAccount import TwitterAccount

from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error


AUDIT_TYPE_TW_CAMPAIGN = 16

class TwitterTailoredAudienceManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterTailoredAudienceManager, self).own(queryset)
        return queryset


class TwitterTailoredAudience(BaseModel):
    tw_targeting_id = models.BigIntegerField(primary_key=True)
    tw_account_id = models.ForeignKey(TwitterAccount, db_column='tw_account_id')
    name = models.CharField(max_length=255)
    audience_size = models.CharField(max_length=255)
    targetable_types = models.TextField(blank=True)
    audience_type = models.CharField(max_length=255)
    targetable = models.NullBooleanField()
    list_type = models.CharField(max_length=255)
    reasons_not_targetable = models.TextField(blank=True)
    partner_source = models.CharField(max_length=255)
    is_owner = models.NullBooleanField()
    permission_level = models.CharField(max_length=255)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None)

    objects = TwitterTailoredAudienceManager()
    objects_raw = models.Manager()
    # permission_check = True

    search_args = ('name', 'tw_account_id', )

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_tailored_audience'
        app_label = 'restapi'


    @classmethod
    def fetch_tailored_audience(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['data'] = []
        res['success'] = False
        account_id = data.get('account_id')

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

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                        oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            account = client.accounts(account_id)
            resource = '/{api_version}/accounts/{account_id}/tailored_audiences?count=1000'.format(api_version=settings.TW_API_VERSION,
                                                                                        account_id=account_id)
            response = Request(client, 'get', resource).perform()
            tailored_audiences = response.body['data']

            next_cursor = None
            if response.body['next_cursor'] and response.body['next_cursor'] is not 0:
                next_cursor = response.body['next_cursor']
                while next_cursor is not 0:
                    resource = '/{api_version}/accounts/{account_id}/tailored_audiences?cursor={next_cursor}&count=1000'.format(api_version=settings.TW_API_VERSION,
                                                                                        account_id=account_id, next_cursor=next_cursor)
                    response = Request(client, 'get', resource).perform()
                    next_cursor = response.body['next_cursor'] or 0
                    tailored_audiences += response.body['data']

            api_domain = 'https://ads.twitter.com'

            resource = '/accounts/{account_id}/apps.json'.format(account_id=account_id)
            response = Request(client, 'get', resource, domain=api_domain).perform()

            apps = response.body.get('apps_info', {})
            app_table = []
            for (k, v) in apps.iteritems():
                app_store_identifier = v.get('app_store_identifier')
                app_name = v.get('title')
                if app_store_identifier and app_name:
                    app_table.append({'id': app_store_identifier, 'name': app_name})

            def replace_app_name(app_name):
                for app_info in app_table:
                    app_name = app_name.replace(app_info['id'], app_info['name'])

                return app_name.replace('_', ' ')

            def human_format(num):
                magnitude = 0
                while abs(num) >= 1000:
                    magnitude += 1
                    num /= 1000.0
                # add more suffixes if you need them
                return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

            for audience in tailored_audiences:
                audience['name'] = replace_app_name(audience['name'])
                if audience['audience_size']:
                    audience['audience_size'] = human_format(audience['audience_size'])
                    audience['name'] = '%s (%s users)' % (audience['name'], audience['audience_size'])

            res['success'] = True
            res['data'] = tailored_audiences

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
                for index, audience in enumerate(res['data'], start=0):
                    audience_res = self.sync_tailored_audience(account_id_int, audience)
                    if 'success' in audience_res and audience_res['success'] is True:
                        if audience_res['type'] == 'existing':
                            existing_count +=1
                        if audience_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1

                    elif 'success' in audience_res and audience_res['success'] is False:
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
                audience_res = self.sync_tailored_audience(account_id_int, res['data'])

                if 'success' in audience_res and audience_res['success'] is True:
                    res['data'] = audience_res['data']
                    res['sync']['success'] = audience_res['success']
                    res['sync']['type'] = {}
                    res['sync']['type'][audience_res['type']] = 1
                    res['sync']['total'] = 1

                elif 'success' in audience_res and audience_res['success'] is False:
                    res['data'] = audience_res['data']
                    res['sync']['success'] = audience_res['success']
                    res['sync']['message'] = audience_res['message']
        return res


    @classmethod
    def sync_tailored_audience(self, tw_account_id, data, manage_campaign_id=None):
        res = {}
        res['data'] = data
        res['success'] = False
        res['os_platform'] = 'web'
        tailored_audience_id_int = base36_to_int(data['id'])

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
            m_tw_tailored_audience = TwitterTailoredAudience.objects_raw.get(tw_account_id=m_tw_account, tw_targeting_id=tailored_audience_id_int)
        except TwitterTailoredAudience.DoesNotExist:
            res['type'] = 'new'
            m_tw_tailored_audience = TwitterTailoredAudience(tw_account_id=m_tw_account, tw_targeting_id=tailored_audience_id_int)

        if m_tw_tailored_audience is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter Tailored Audience"
            }
            return res
        
        m_tw_tailored_audience.name = data['name']
        m_tw_tailored_audience.targetable = data['targetable']
        m_tw_tailored_audience.audience_size  = data['audience_size']
        m_tw_tailored_audience.targetable_types = json.dumps(data['targetable_types'])
        m_tw_tailored_audience.audience_type = data['audience_type']
        m_tw_tailored_audience.targetable = data['targetable']
        m_tw_tailored_audience.list_type = data['list_type']
        m_tw_tailored_audience.reasons_not_targetable = json.dumps(data['reasons_not_targetable'])
        m_tw_tailored_audience.partner_source = data['partner_source']
        m_tw_tailored_audience.is_owner = data['is_owner']
        m_tw_tailored_audience.permission_level = data['permission_level']
        m_tw_tailored_audience.last_update = data['updated_at']

        if data['deleted'] == True:
            m_tw_tailored_audience.status = STATUS_ARCHIVED

        m_tw_tailored_audience.save_raw()
        res['success'] = True
        return res

audit.AuditLogger.register(TwitterTailoredAudience, audit_type=AUDIT_TYPE_TW_CAMPAIGN, check_delete='physical_delete')
