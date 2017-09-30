import json
from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.Advertiser import Advertiser
from restapi.models.twitter.TwitterUser import TwitterUser

import twitter
from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error
import traceback

class TwitterAccountManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterAccountManager, self).own(queryset)
        return queryset


class TwitterAccount(BaseModel):
    tw_account_id = models.BigIntegerField(primary_key=True)
    tw_twitter_user_id =  models.ForeignKey(TwitterUser, db_column='tw_twitter_user_id', related_name="tw_account_tw_twitter_user")
    promotable_user_id = models.ForeignKey(TwitterUser, db_column='promotable_user_id', related_name="tw_account_tw_promotable_user")
    advertiser_id = models.ForeignKey(Advertiser, db_column='advertiser_id')
    is_manage = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterAccountManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_account'
        app_label = 'restapi'


    @classmethod
    def fetch_accounts(self, data, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        res = {}
        account_id = data.get('account_id')

        if isinstance(account_id,(int,long)):
            account_id = int_to_base36(account_id)

        if account_id is None:
            res = {
                'data': {},
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token, oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX

        try:
            account = client.accounts(account_id)
            resource = '/{api_version}/accounts/{account_id}'.format(api_version=settings.TW_API_VERSION, account_id=account_id)
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
        return res
