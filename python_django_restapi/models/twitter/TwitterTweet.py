import json
from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterUser import TwitterUser
from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error

# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/campaigns
_cache = {}
class TwitterTweetManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterTweetManager, self).own(queryset)
        return queryset


class TwitterTweet(BaseModel):
    tw_tweet_id = models.BigIntegerField(primary_key=True)
    tw_twitter_user_id  = models.BigIntegerField()
    text = models.TextField(blank=True)

    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterTweetManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_tweet'
        app_label = 'restapi'

    @classmethod
    def fetch_tweet(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN,
                    oauth_secret=settings.TW_ACCESS_SECRET):
        res = {}
        res['success'] = True
        account_id = data.get('account_id')
        tweet_id = data.get('tweet_id')

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id = int_to_base36(account_id)

        if not _cache.get(account_id):
            try:
                tw_account = TwitterAccount.objects_raw.filter(tw_account_id=account_id_int).first()
                if tw_account.promotable_user_id.tw_twitter_user_id:
                    _cache[account_id] = tw_account.promotable_user_id.tw_twitter_user_id
            except TwitterUser.DoesNotExist:
                _cache[account_id] = 0
            except TwitterAccount.DoesNotExist:
                _cache[account_id] = 0

        if account_id is None:
            res = {
                'data': {},
                'success': False,
                'message': "Missing Twitter Account ID"
            }
            return res

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token, oauth_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        try:
            api_domain = 'https://api.twitter.com'
            resource = '/{api_version}/statuses/show.json?id={tweet_id}'.format(api_version="1.1", tweet_id=tweet_id)
            response = Request(client, 'get', resource, domain=api_domain).perform()
            entities = response.body['entities']

            #print response.headers['x-rate-limit-remaining']
            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            expanded_url = None
            if entities and entities['urls'] and entities['urls'][0] and entities['urls'][0]['expanded_url']:
                expanded_url = entities['urls'][0]['expanded_url']

            account = client.accounts(account_id)
            as_user_id = ('?as_user_id=%s' % _cache[account_id]) if _cache[account_id] else ''
            resource = '/{api_version}/accounts/{account_id}/tweet/preview/{tweet_id}{as_user_id}'.format(api_version=settings.TW_API_VERSION, account_id=account.id, tweet_id=tweet_id, as_user_id=as_user_id)
            response = Request(client, 'get', resource).perform()
            res['data'] = response.body['data']
            res['card_url'] = expanded_url

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

