from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES, TW_PRODUCT_TYPES, TW_PLACEMENTS, TW_OBJECTIVES, TW_BID_TYPES, TW_BID_UNITS, TW_OPTIMIZATIONS, TW_CHARGE_BYS, STATUS_ARCHIVED
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterTargetingModels import TwitterTargeting, TwitterEvent, TwitterBehavior
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.serializers.validators.BaseValidator import BaseValidator
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.models.fields import ZeroDateTimeField
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.twitter.TwitterPromotedTweetSerializer import TwitterPromotedTweetSerializer
from restapi.serializers.twitter.TwitterTargetingSerializer import TwitterTargetingDetailSerializer
from restapi.views.twitter.helper import human_format
from twitter_ads.client import Client
from twitter_ads.http import Request
from django.conf import settings
from django.utils.http import int_to_base36, base36_to_int
from restapi.models.twitter.TwitterTargetingModels import *
# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/campaigns


type_names = {
            2: 'location',
            3: 'platform',
            4: 'device',
            5: 'wifi_only',
            8: 'followers_of_user',
            9: 'SIMILAR_TO_FOLLOWERS_OF_USER',
            10: 'board_keyword',
            11: 'UNORDERED_KEYWORD',
            12: 'phrase_keyword',
            13: 'EXACT_KEYWORD',
            14: 'app_category',
            15: 'carrier',
            16: 'os_version',
            17: 'user_interest',
            19: 'tv_genre',
            20: 'tv_channel',
            21: 'tv_show',
            22: 'behavior',
            23: 'event'
        }

platform_dep_cls_names = {
    'device': TwitterDevice,
    'os_version': TwitterOsVersion#,
    #'app_category': TwitterAppCategory
}

class TwitterLineItemSerializer(BaseModelSerializer):
    tw_campaign_id = PKRelatedField(queryset=TwitterCampaign.objects_raw.all())
    name = serializers.CharField(required=True, allow_blank=False)
    currency = serializers.CharField(required=True, allow_blank=False)
    product_type = ChoiceCaseInsensitiveField(choices=TW_PRODUCT_TYPES, required=False)
    placements = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    primary_web_event_tag = serializers.CharField(required=True, allow_blank=False)
    objective = ChoiceCaseInsensitiveField(choices=TW_OBJECTIVES, required=False)
    bid_amount_local_micro = serializers.CharField(required=True, allow_blank=False)
    bid_amount_computed = serializers.CharField(required=True, allow_blank=False)
    bid_override = serializers.NullBooleanField()
    bid_type = ChoiceCaseInsensitiveField(choices=TW_BID_TYPES, required=False)
    bid_unit = ChoiceCaseInsensitiveField(choices=TW_BID_UNITS, required=False)
    optimization = ChoiceCaseInsensitiveField(choices=TW_OPTIMIZATIONS, required=False)
    charge_by = ChoiceCaseInsensitiveField(choices=TW_CHARGE_BYS, required=False)
    categories = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    tracking_tags = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    automatically_select_bid = serializers.NullBooleanField()
    total_budget_amount_local_micro  = serializers.CharField(required=False, allow_blank=True)
    daily_budget_amount_local_micro = serializers.CharField(required=False, allow_blank=True)
    promoted_tweets = serializers.SerializerMethodField()
    targeting = serializers.SerializerMethodField()
    tw_campaign_name = serializers.SerializerMethodField()
    cpi_target_goal = serializers.SerializerMethodField()
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)
    advertiser_id = serializers.SerializerMethodField()
    campaign_id = serializers.SerializerMethodField()
    tailored_audience = serializers.SerializerMethodField()
    class Meta:
        model = TwitterLineItem
        fields = ('tw_line_item_id',
                  'tw_campaign_id',
                  'tw_campaign_name',
                  'advertiser_id',
                  'campaign_id',
                  'name',
                  'currency',
                  'start_time',
                  'end_time',
                  'product_type',
                  'placements',
                  'primary_web_event_tag',
                  'objective',
                  'bid_amount_local_micro',
                  'bid_amount_computed_reason',
                  'bid_amount_computed',
                  'bid_override',
                  'bid_type',
                  'bid_unit',
                  'optimization',
                  'charge_by',
                  'categories',
                  'tracking_tags',
                  'automatically_select_bid',
                  'total_budget_amount_local_micro',
                  'daily_budget_amount_local_micro',
                  'status',
                  'created_at',
                  'last_update',
                  'promoted_tweets',
                  'targeting',
                  'cpi_target_goal',
                  'tailored_audience'
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterLineItem.objects_raw.all(),
                fields=('tw_capaign_id', 'name')
            )
        ]

    def get_advertiser_id(self, instance):
        return instance._advertiser_id

    def get_campaign_id(self, instance):
        return instance._campaign_id

    def get_tw_campaign_name(self, instance):
        return instance.tw_campaign_id.name

    def get_promoted_tweets(self, instance):
        promoted_tweets = TwitterPromotedTweet.objects.filter(tw_line_item_id=instance.tw_line_item_id).all()
        return TwitterPromotedTweetSerializer(promoted_tweets, many=True).data

    def get_cpi_target_goal(self, instance):
        res = TwitterRevmap.objects.filter(tw_line_item_id=instance.tw_line_item_id).first()
        if res:
            return res.opt_value
        else:
            return ''

    def get_targeting(self, instance):
        targetings = TwitterTargeting.objects.filter(tw_line_item_id=instance.tw_line_item_id).exclude(tw_targeting_type=18).all()

        ret = {}
        for t in targetings:
            type_name = type_names.get(t.tw_targeting_type)
            # if targeting_type is not supported one, continue
            if not type_name:
                continue
            if not ret.get('platform') and platform_dep_cls_names.get(type_name):
                _cls = platform_dep_cls_names[type_name]
                item = _cls.objects_raw.filter(tw_targeting_id=t.tw_targeting_id).first()
                if item:
                    ret['platform'] = [item.platform]

            if not ret.get(type_name):
                ret[type_name] = []
            if t.tw_targeting_type == 22:
                behavior = TwitterBehavior.objects_raw.filter(tw_targeting_id=t.tw_targeting_id).first()
                """
                if behavior:
                    temp = []
                    taxonomy = behavior.tw_behavior_taxonomy
                    if taxonomy.parent:
                        temp.append(taxonomy.parent.name)
                    temp.append(taxonomy.name)
                    temp.append(behavior.name)

                    ret[type_name].append(' > '.join(temp))
                """
                ret[type_name].append(behavior.name)
            elif t.tw_targeting_type == 23:
                event = TwitterEvent.objects_raw.filter(tw_targeting_id=t.tw_targeting_id).first()
                if event:
                    ret[type_name].append(event.name)
            else:
                ret[type_name].append(t.name)

        return ret

    def get_tailored_audience(self, instance):
        res = {}
        targetings = TwitterTargeting.objects.filter(tw_line_item_id=instance.tw_line_item_id, tw_targeting_type=18).all()
        for targeting in targetings:
            if not res.get(targeting.name):
                res[targeting.name] = []
            audience = TwitterTailoredAudience.objects.filter(tw_targeting_id=targeting.tw_targeting_id).first()
            if audience:
                if not targeting.targeting_params:
                    # for fallback, since all app install tailored audiences' targeting_params is empty
                    _type = 'Excluded'
                else:
                    if 'EXCLUDED' in targeting.targeting_params:
                        _type = 'Excluded'
                    else:
                        _type = 'Included'

                res[targeting.name].append("<b>%s</b>: %s" % (_type, audience.name))

        return res


class TwitterLineItemDetailSerializer(BaseModelSerializer):
    targeting = serializers.SerializerMethodField()
    cpi_target_goal = serializers.SerializerMethodField()
    tw_account_id = serializers.SerializerMethodField()
    tweet_ids = serializers.SerializerMethodField()
    class Meta:
        model = TwitterLineItem
        fields = ('tw_line_item_id',
                  'tw_campaign_id',
                  'tw_account_id',
                  'bid_amount_computed',
                  'bid_amount_local_micro',
                  'bid_type',
                  'bid_amount_computed_reason',
                  'name',
                  'status',
                  'objective',
                  'targeting',
                  'cpi_target_goal',
                  'tweet_ids'
        )


    def get_tweet_ids(self, instance):
        tweets = TwitterPromotedTweet.objects_raw.filter(tw_line_item_id=instance.tw_line_item_id).exclude(status=STATUS_ARCHIVED)
        res = []
        for t in tweets:
            res.append(str(t.tw_tweet_id))
        return res

    def get_tw_account_id(self, instance):
        return instance.tw_campaign_id.tw_account_id.tw_account_id

    def get_cpi_target_goal(self, instance):
        res = TwitterRevmap.objects.filter(tw_line_item_id=instance.tw_line_item_id).first()
        if res:
            return res.opt_value
        else:
            return ''

    def get_targeting(self, instance):
        targetings = TwitterTargeting.objects_raw.filter(tw_line_item_id=instance.tw_line_item_id).all().order_by('tw_targeting_type')

        user_ids = [t.targeting_value for t in TwitterTargeting.objects_raw.filter(tw_line_item_id=instance.tw_line_item_id,tw_targeting_type=9).all()]
        event_ids = [int_to_base36(int(t.tw_targeting_id)) for t in TwitterTargeting.objects_raw.filter(tw_line_item_id=instance.tw_line_item_id,tw_targeting_type=23).all()]

        i = 0
        api_domain = 'https://api.twitter.com'
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, settings.TW_ACCESS_TOKEN,
                                settings.TW_ACCESS_SECRET)
        targeting_json = TwitterTargetingDetailSerializer(targetings, many=True).data
        try:
            while i < len(user_ids):
                temp = user_ids[i:i+100]
                i += 100
                resource = '/1.1/users/lookup.json?user_id=%s' % ','.join(temp)
                result = Request(client, 'get', resource, domain=api_domain).perform()
                for r in result.body:
                    extra = dict(followers_count_str=human_format(r['followers_count']), targeting_value=r['id_str'], name=r['name'], profile_image_url=r['profile_image_url'], screen_name=r['screen_name'])
                    for k, target in enumerate(targeting_json):
                        if str(target['targeting_value']) == str(r['id']):
                            targeting_json[k]['extra'] = extra
        except Exception as e:
            print str(e)
            print 'fetching users failed'
        try:
            if len(event_ids) > 0:
                resource = '/%s/targeting_criteria/events?ids=%s' % (settings.TW_API_VERSION, ','.join(event_ids))
                result = Request(client, 'get', resource).perform()
                for r in result.body['data']:
                    _id = str(base36_to_int(r['id']))
                    event_type = r['event_type']
                    event_type = event_type.replace('MUSIC_AND_', '')
                    event_type = event_type.replace('_', ' ').capitalize()
                    extra = dict(id=_id, name=r['name'], category=event_type)
                    for k, target in enumerate(targeting_json):
                        if str(target['tw_targeting_id']) == _id:
                            targeting_json[k]['extra'] = extra
        except:
            print 'fetching events failed'
        return targeting_json