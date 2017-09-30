from rest_framework import serializers
from restapi.models.Source import Source
from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign
from restapi.models.choices import PLACEMENT_TYPE_CHOICES
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.validators.BaseValidator import BaseValidator
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.BaseReadonlySerializer import BaseReadonlySerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.IntRelationField import IntRelationField


class BaseBidderListSerializer(BaseReadonlySerializer):
    # pylint: disable=invalid-name
    id = serializers.IntegerField()
    advertiser_id = serializers.IntegerField()
    campaign_id = serializers.IntegerField()
    ad_group_id = serializers.IntegerField()
    source_id = serializers.IntegerField()
    campaign = serializers.CharField()
    ad_group = serializers.CharField()
    last_update = DateTimeField()
    placement_type = serializers.CharField()
    placement_id = serializers.CharField()
    size = serializers.CharField()
    tag = serializers.CharField()


class BaseBidderListIdsSerializer(BaseModelSerializer):
    campaign_id = IntRelationField(required=False, related_model=Campaign, allow_zero=True)
    ad_group_id = IntRelationField(required=False, related_model=AdGroup, allow_zero=True)
    source_id = IntRelationField(required=True, related_model=Source, allow_zero=True)
    last_update = DateTimeField(read_only=True)
    placement_type = ChoiceCaseInsensitiveField(choices=PLACEMENT_TYPE_CHOICES, required=False)
    placement_id = serializers.CharField()
    size = serializers.CharField(required=False)
    tag = serializers.CharField(required=False, allow_blank=True)

    def is_valid(self, *args, **kwargs):
        errors = {}
        for field in ['ad_id', 'ad_group_id', 'campaign_id', 'source_id']:
            if field in self.fields and not BaseValidator.is_digit_or_none(self, field):
                errors[field] = 'Field should be a number'
        if errors:
            raise serializers.ValidationError(errors)

        valid = super(BaseBidderListIdsSerializer, self).is_valid(*args, **kwargs)
        campaign_id = self.validated_data.get('campaign_id', None)
        ad_group_id = self.validated_data.get('ad_group_id', None)
        source_id = self.validated_data.get('source_id', None)
        errors_key = {}
        if campaign_id and ad_group_id:
            true_campaign_id = AdGroup.objects_raw.get(pk=ad_group_id).campaign_id.pk
            if int(campaign_id) != int(true_campaign_id):
                message = 'Selected ad group(%s/%s) and campaign(%s) do not match' % (ad_group_id,
                                                                                      true_campaign_id,
                                                                                      campaign_id)
                errors_key['ad_group_id, campaign_id'] = message

        if ad_group_id and not campaign_id:
            self.validated_data['campaign_id'] = Campaign.objects.get(adgroup=ad_group_id).campaign_id

        if not source_id or source_id == 0:
            errors_key['source_id'] = "You must select Source ID. Valid range from 1 to {0} inclusively" \
                .format(Source.objects.count())

        size = self.validated_data.get('size', None)
        if size and size == '375x50':
            errors_key['size'] = '375x50 size is currently unsupported'

        if errors_key:
            raise serializers.ValidationError(errors_key)

        return valid
