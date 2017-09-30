import json
from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from django.conf import settings
from restapi.email import send_twitter_alert_email
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED, STATUS_ARCHIVED, TW_CUSTOM_CTA, TW_CARD_TYPE
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.twitter.TwitterAccount import TwitterAccount

from twitter_ads.client import Client
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error

# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/campaigns

class TwitterAppCardManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterAppCardManager, self).own(queryset)
        return queryset


class TwitterAppCard(BaseModel):
    tw_app_card_id = models.BigIntegerField(primary_key=True)
    tw_account_id = models.ForeignKey(TwitterAccount, db_column='tw_account_id')
    name = models.CharField(max_length=255)
    card_type = models.CharField(max_length=20, choices=TW_CARD_TYPE, default='app_card')
    preview_url = models.CharField(max_length=255)
    app_country_code = models.CharField(max_length=255)
    iphone_app_id = models.CharField(max_length=255)
    ipad_app_id = models.CharField(max_length=255)
    googleplay_app_id = models.CharField(max_length=255)
    deep_link = models.CharField(max_length=255)
    custom_cta = models.CharField(max_length=255, choices=TW_CUSTOM_CTA)
    custom_icon_media_id = models.CharField(max_length=255)
    custom_app_description = models.CharField(max_length=255)
    image_media_id = models.CharField(max_length=255)
    wide_app_image = models.CharField(max_length=255)
    wide_app_image_media_id = models.CharField(max_length=255)
    video_id = models.CharField(max_length=255)
    video_url = models.CharField(max_length=255)
    video_poster_url = models.CharField(max_length=255)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterAppCardManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_app_card'
        app_label = 'restapi'


    @classmethod
    def fetch_app_cards(self, data, syncData=False, oauth_token=settings.TW_ACCESS_TOKEN,
                        oauth_secret=settings.TW_ACCESS_SECRET):
        res = {}
        account_id = data.get('account_id')

        if isinstance(account_id,(int,long)):
            account_id_int = account_id
            account_id = int_to_base36(account_id)
        else:
            account_id_int = base36_to_int(account_id)

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
            res['data'] = []
            account = client.accounts(account_id)
            resource = '/{api_version}/accounts/{account_id}/cards/app_download'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
            response = Request(client, 'get', resource).perform()
            for card in response.body['data']:
                res['data'].append(card)

            resource = '/{api_version}/accounts/{account_id}/cards/image_app_download'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
            response = Request(client, 'get', resource).perform()
            for card in response.body['data']:
                res['data'].append(card)

            resource = '/{api_version}/accounts/{account_id}/cards/video_app_download'.format(api_version=settings.TW_API_VERSION, account_id=account.id)
            response = Request(client, 'get', resource).perform()

            if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
                send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

            for card in response.body['data']:
                res['data'].append(card)
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
                for index, api_app_card in enumerate(res['data'], start=0):
                    app_card_res = self.sync_app_card(account_id_int, api_app_card)

                    if 'success' in app_card_res and app_card_res['success'] is True:
                        if app_card_res['type'] == 'existing':
                            existing_count +=1
                        if app_card_res['type'] == 'new':
                            new_count +=1
                        sync_success += 1
                    elif 'success' in app_card_res and app_card_res['success'] is False:
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
                app_card_res = self.sync_app_card(account_id_int, res['data'])
                if 'success' in app_card_res and app_card_res['success'] is True:
                    res['data'] = app_card_res['data']
                    res['sync']['success'] = app_card_res['success']
                    res['sync']['type'] = {}
                    res['sync']['total'] = 1
                    res['sync']['type'][app_card_res['type']] = 1
                    # sync_success

                if 'success' in app_card_res and app_card_res['success'] is False:
                    res['data'] = app_card_res['data']
                    res['sync']['success'] = app_card_res['success']
                    res['sync']['message'] = app_card_res['message']

        return res

    @classmethod
    def sync_app_card(self, tw_account_id, data):
        res = {}
        res['data'] = data
        res['success'] = False
        appcard_id_int = base36_to_int(data['id'])

        if isinstance(tw_account_id, TwitterAccount):
            m_tw_account = tw_account_id
        else:
            m_tw_account = TwitterAccount.objects_raw.filter(tw_account_id=tw_account_id).first()

        if m_tw_account is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter AppCard. Cannot find Twitter Account"
            }
            return res

        try:
            res['type'] = 'existing'
            m_tw_appcard = TwitterAppCard.objects_raw.get(tw_account_id=m_tw_account, tw_app_card_id=appcard_id_int)
        except TwitterAppCard.DoesNotExist:
            res['type'] = 'new'
            m_tw_appcard = TwitterAppCard(tw_account_id=m_tw_account, tw_app_card_id=appcard_id_int)

        if m_tw_appcard is None:
            res = {
                'data': {},
                'success': False,
                'message': "Error syncing Twitter AppCard"
            }
            return res

        if data['name']:
            m_tw_appcard.name = data['name']

        if data['card_type'] == 'IMAGE_APP_DOWNLOAD':
            m_tw_appcard.card_type = 'image'
        elif data['card_type'] == 'APP_DOWNLOAD':
            m_tw_appcard.card_type = 'app_card'
        elif data['card_type'] == 'VIDEO_APP_DOWNLOAD':
            m_tw_appcard.card_type = 'video'
            if data['video_url']:
                m_tw_appcard.video_url = data['video_url']

        if data['preview_url']:
            m_tw_appcard.preview_url = data['preview_url']
        if data['app_country_code']:
            m_tw_appcard.app_country_code = data['app_country_code']

        if 'iphone_app_id' in data and data['iphone_app_id']:
            m_tw_appcard.iphone_app_id = data['iphone_app_id']
        if 'ipad_app_id' in data and  data['ipad_app_id']:
            m_tw_appcard.iphone_app_id = data['ipad_app_id']
        if 'googleplay_app_id' in data and  data['googleplay_app_id']:
            m_tw_appcard.iphone_app_id = data['googleplay_app_id']
        if 'deep_link' in data and data['deep_link']:
            m_tw_appcard.deep_link = data['deep_link']
        if 'app_cta' in data and data['app_cta']:
            m_tw_appcard.custom_cta = data['app_cta']

        if 'custom_icon_media_id' in data and data['custom_icon_media_id']:
            m_tw_appcard.custom_icon_media_id = data['custom_icon_media_id']
        if 'custom_app_description' in data and data['custom_app_description']:
            m_tw_appcard.custom_app_description = data['custom_app_description']
        if 'image_media_id' in data and data['image_media_id']:
            m_tw_appcard.image_media_id = data['image_media_id']
        if 'wide_app_image_media_id' in data and data['wide_app_image_media_id']:
            m_tw_appcard.wide_app_image_media_id = data['wide_app_image_media_id']
        if 'wide_app_image' in data and data['wide_app_image']:
            m_tw_appcard.wide_app_image = data['wide_app_image']
        if 'video_id' in data and data['video_id']:
            m_tw_appcard.video_id = data['video_id']
        if 'video_url' in data and data['video_url']:
            m_tw_appcard.video_url = data['video_url']
        if 'video_poster_url' in data and data['video_poster_url']:
            m_tw_appcard.video_poster_url = data['video_poster_url']

        if data['deleted'] == False:
            m_tw_appcard.status = STATUS_ENABLED
        if data['deleted'] == True:
            m_tw_appcard.status = STATUS_ARCHIVED

        m_tw_appcard.save_raw()

        res['success'] = True
        return res
