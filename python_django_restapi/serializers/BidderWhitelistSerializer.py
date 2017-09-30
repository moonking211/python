from restapi.models.BidderWhitelist import BidderWhitelist, BidderWhitelistIds
from restapi.serializers.BaseBidderListSerializer import BaseBidderListSerializer, BaseBidderListIdsSerializer
from restapi.models.choices import SIZE_CHOICES

from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField

class BidderWhitelistSerializer(BaseBidderListSerializer):
    # pylint: disable=old-style-class
    class Meta:
        model = BidderWhitelist


class BidderWhitelistIdsSerializer(BaseBidderListIdsSerializer):
    size = ChoiceCaseInsensitiveField(choices=SIZE_CHOICES, required=False)


    # pylint: disable=old-style-class
    class Meta:
        model = BidderWhitelistIds
