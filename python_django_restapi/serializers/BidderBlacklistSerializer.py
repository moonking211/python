from rest_framework import serializers
from restapi.models.BidderBlacklist import BidderBlacklist
from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.serializers.fields.MultipleSizeChoiceField import MultipleSizeChoiceField
from restapi.serializers.BaseBidderListSerializer import BaseBidderListSerializer
from restapi.serializers.BaseBidderListSerializer import BaseBidderListIdsSerializer

from restapi.models.choices import SIZE_CHOICES


class BidderBlacklistSerializer(BaseBidderListSerializer):
    # pylint: disable=old-style-class
    class Meta:
        model = BidderBlacklist


class BidderBlacklistIdsSerializer(BaseBidderListIdsSerializer):
    size = MultipleSizeChoiceField(choices=SIZE_CHOICES, required=False)

    # pylint: disable=old-style-class
    class Meta:
        model = BidderBlacklistIds

    def is_valid(self, *args, **kwargs):
        errors_key = {}
        valid = super(BidderBlacklistIdsSerializer, self).is_valid(*args, **kwargs)
        campaign_id = self.validated_data.get('campaign_id', None)
        ad_group_id = self.validated_data.get('ad_group_id', None)

        if ad_group_id is not None and ad_group_id != 0:
            if campaign_id is None or campaign_id == 0:
                errors_key['campaign_id'] = 'Field is required'

        if errors_key:
            raise serializers.ValidationError(errors_key)

        return valid
