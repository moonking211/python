from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.DateTimeField import ZeroDateTimeField
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
# https://dev.twitter.com/ads/reference/get/accounts/%3Aaccount_id/campaigns

class TwitterCampaignSerializer(BaseModelSerializer):
    tw_account_id = PKRelatedField(queryset=TwitterAccount.objects_raw.all())
    campaign_id = PKRelatedField(queryset=Campaign.objects_raw.all())
    name = serializers.CharField(required=True, allow_blank=False)
    funding_instrument_id = serializers.CharField(required=True, allow_blank=True)
    start_time = ZeroDateTimeField(required=False, allow_null=True)
    end_time = ZeroDateTimeField(required=False, allow_null=True)
    standard_delivery = serializers.NullBooleanField()
    frequency_cap = serializers.IntegerField(required=False, allow_null=True)
    duration_in_days = ChoiceCaseInsensitiveField(choices=[1, 7, 30], required=False, allow_null=True)
    total_budget_amount_local_micro = serializers.CharField(required=False, allow_blank=True)
    daily_budget_amount_local_micro = serializers.CharField(required=True, allow_blank=True)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)
    advertiser_id = serializers.SerializerMethodField()
    cpi_target_goal = serializers.SerializerMethodField()
    line_item_count = serializers.SerializerMethodField()
    class Meta:
        model = TwitterCampaign
        fields = ('tw_campaign_id',
                  'tw_account_id',
                  'advertiser_id',
                  'campaign_id',
                  'name',
                  'funding_instrument_id',
                  'start_time',
                  'end_time',
                  'frequency_cap',
                  'standard_delivery',
                  'duration_in_days',
                  'total_budget_amount_local_micro',
                  'daily_budget_amount_local_micro',
                  'cpi_target_goal',
                  'line_item_count',
                  'status',
                  'created_at',
                  'last_update')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterCampaign.objects_raw.all(),
                fields=('tw_campaign_id', 'name')
            )
        ]

    def get_advertiser_id(self, instance):
        return instance._advertiser_id

    def get_cpi_target_goal(self, instance):
        res = TwitterRevmap.objects.filter(tw_campaign_id=instance.tw_campaign_id).first()
        if res:
            return res.opt_value
        else:
            return ''

    def get_line_item_count(self, instance):
        return dict(all=TwitterLineItem.objects_raw.filter(tw_campaign_id=instance.pk).count(),
                    active=TwitterLineItem.objects_raw.filter(tw_campaign_id=instance.pk).exclude(status='deleted').count())