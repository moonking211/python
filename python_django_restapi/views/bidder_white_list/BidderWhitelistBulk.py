from restapi.models.BidderWhitelist import BidderWhitelistIds
from restapi.serializers.BidderWhitelistSerializer import BidderWhitelistIdsSerializer
from restapi.views.BaseBulkOperations import BaseBulkOperations


class BidderWhitelistBulk(BaseBulkOperations):
    model = BidderWhitelistIds
    serializer = BidderWhitelistIdsSerializer
