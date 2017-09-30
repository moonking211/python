from rest_framework import serializers

from restapi.models.DiscretePricing import DiscretePricing, DiscretePricingIds
from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign
from restapi.models.choices import DISCRETE_PRICING_SIZE_CHOICES
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.IntRelationField import IntRelationField
from restapi.serializers.BaseBidderListSerializer import BaseBidderListSerializer, BaseBidderListIdsSerializer


class DiscretePricingSerializer(BaseBidderListSerializer):
    created_at = DateTimeField()
    last_update = DateTimeField()
    tag = serializers.CharField()
    rev_value = serializers.DecimalField(max_digits=9, decimal_places=2)

    # pylint: disable=old-style-class
    class Meta:
        model = DiscretePricing


class DiscretePricingIdsSerializer(BaseBidderListIdsSerializer):
    created_at = DateTimeField(read_only=True)
    campaign_id = IntRelationField(required=True, related_model=Campaign, allow_zero=True)
    ad_group_id = IntRelationField(required=True, related_model=AdGroup, allow_zero=True)
    last_update = DateTimeField(read_only=True)
    tag = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    size = serializers.ChoiceField(choices=DISCRETE_PRICING_SIZE_CHOICES, required=False)
    rev_value = serializers.DecimalField(max_digits=9, decimal_places=2)

    # pylint: disable=old-style-class
    class Meta:
        model = DiscretePricingIds

    def is_valid(self, *args, **kwargs):
        errors_key = {}
        valid = super(DiscretePricingIdsSerializer, self).is_valid(*args, **kwargs)
        rev_value = self.validated_data.get('rev_value', None)
        size = self.validated_data.get('size', None)

        if size != 'all':
            errors_key['size'] = "Size: Not valid size. Size must be 'all'"
        if not rev_value or not float(rev_value):
            errors_key['rev_value'] = 'Field is required'
        elif float(rev_value) < 0:
            errors_key['rev_value'] = 'Rev value could not be negative'

        # CPI and CPC only [AMMYM-1713]
        campaign_id = self.validated_data.get('campaign_id', None)
        if not campaign_id:
            errors_key['campaign_id'] = 'Field is required'
        ad_group_id = self.validated_data.get('ad_group_id', None)
        if not ad_group_id:
            errors_key['ad_group_id'] = 'Field is required'
        source_id = self.validated_data.get('source_id', None)
        if not source_id:
            errors_key['source_id'] = 'Field is required'


        if ad_group_id:
            ad_group = AdGroup.objects.get(pk=ad_group_id)
            if not ad_group.revmap_rev_type in ['install', 'click']:
                errors_key['ad_group_id'] = 'Discrete Pricing can be set ONLY for CPI and CPC Ad Groups'
        elif not errors_key:
            queryset = AdGroup.objects.all()
            if campaign_id:
                queryset = queryset.filter(campaign_id__id=campaign_id)
                error_ids = []
                for ad_group in queryset:
                    if not ad_group.revmap_rev_type in ['install', 'click']:
                        error_ids.append(str(ad_group.pk))
                if error_ids:
                    errors_key['campaign_id'] = 'Discrete Pricing can be set ONLY for CPI and CPC Ad Groups ({})'.format(",".join(error_ids))

        if errors_key:
            raise serializers.ValidationError(errors_key)

        return valid
