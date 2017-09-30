from rest_framework import serializers

from restapi.models.Ad import Ad
from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign
from restapi.models.CustomHint import CustomHint, CustomHintIds
from restapi.models.choices import CUSTOM_HINT_SIZE_CHOICES, INFLATOR_TYPE_CHOICES
from restapi.serializers.fields.IntRelationField import IntRelationField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.fields.DateTimeField import WideRangeDateTimeField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.BaseBidderListSerializer import BaseBidderListSerializer, BaseBidderListIdsSerializer


class CustomHintSerializer(BaseBidderListSerializer):
    ad_id = serializers.IntegerField()
    campaign_id = PKRelatedField(queryset=Campaign.objects_raw.all())
    ad_group_id = PKRelatedField(queryset=AdGroup.objects_raw.all())

    # pylint: disable=invalid-name
    ad = serializers.CharField()
    start_date = WideRangeDateTimeField()
    end_date = WideRangeDateTimeField()
    last_update = DateTimeField()
    tag = serializers.CharField()
    inflator_type = serializers.CharField()
    inflator = serializers.DecimalField(max_digits=9, decimal_places=6)
    priority = serializers.IntegerField()
    max_frequency = serializers.IntegerField()
    frequency_interval = serializers.IntegerField()

    # pylint: disable=old-style-class
    class Meta:
        model = CustomHint


class CustomHintIdsSerializer(BaseBidderListIdsSerializer):
    ad_id = IntRelationField(required=False, related_model=Ad, allow_zero=True)
    start_date = WideRangeDateTimeField(required=False)
    end_date = WideRangeDateTimeField(required=True)
    last_update = DateTimeField(read_only=True)
    tag = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    inflator_type = serializers.ChoiceField(choices=INFLATOR_TYPE_CHOICES, required=False, allow_null=True)
    size = serializers.ChoiceField(choices=CUSTOM_HINT_SIZE_CHOICES, required=False)
    inflator = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    priority = serializers.IntegerField(required=False)
    max_frequency = serializers.IntegerField(required=False)
    frequency_interval = serializers.IntegerField(required=False)


    # pylint: disable=old-style-class
    class Meta:
        model = CustomHintIds

    def is_valid(self, *args, **kwargs):
        errors_key = {}
        valid = super(CustomHintIdsSerializer, self).is_valid(*args, **kwargs)
        ad_id = self.validated_data.get('ad_id', None)
        campaign_id = self.validated_data.get('campaign_id', None)
        ad_group_id = self.validated_data.get('ad_group_id', None)

        if ad_id:
            ad_id = int(ad_id)
            # pylint: disable=invalid-name
            ad = Ad.objects_raw.get(pk=ad_id)
            true_ad_group = ad.ad_group_id
            true_ad_group_id = int(true_ad_group.pk)
            true_campaign = ad.ad_group_id.campaign_id
            true_campaign_id = int(true_campaign.pk)

            if ad_group_id:
                if true_ad_group_id != int(ad_group_id):
                    message = 'Selected ad(%s/%s) and ad group(%s) do not match' % (ad_id,
                                                                                    true_ad_group_id,
                                                                                    ad_group_id)
                    errors_key['ad_id, ad_group_id'] = message

            if campaign_id:
                if true_campaign_id != int(campaign_id):
                    message = 'Selected ad(%s/%s) and campaign(%s) do not match' % (ad_id,
                                                                                    true_campaign_id,
                                                                                    campaign_id)
                    errors_key['ad_id, campaign_id'] = message

        # inflator / inflator_type
        inflator = self.validated_data.get('inflator', None)
        inflator_type = self.validated_data.get('inflator_type', None)
        if inflator is not None and not inflator_type:
            errors_key['inflator_type'] = 'Field is required if "inflator" field contain data'
        elif inflator_type and not inflator and inflator != 0:
            errors_key['inflator'] = 'Field is required if "inflator_type" field contain data'

        # max_frequency / frequency_interval
        max_frequency = self.validated_data.get('max_frequency', None)
        start_date = self.validated_data.get('start_date', None)
        frequency_interval = self.validated_data.get('frequency_interval', None)
        if max_frequency and not frequency_interval:
            errors_key['frequency_interval'] = 'Field is required if "max_frequency" field contain data'

        elif frequency_interval and not max_frequency:
            errors_key['max_frequency'] = 'Field is required if "frequency_interval" field contain data'

        if max_frequency and not start_date:
            errors_key['start_date'] = 'Field is required if "max_frequency" field contain data'

        source_id = self.validated_data.get('source_id', None)
        if source_id is None or source_id == 0:
            errors_key['source_id'] = 'Field is required'
            
        if ad_group_id is not None and ad_group_id != 0:
            if campaign_id is None or campaign_id == 0:
                errors_key['campaign_id'] = 'Field is required'

        if errors_key:
            raise serializers.ValidationError(errors_key)

        return valid
