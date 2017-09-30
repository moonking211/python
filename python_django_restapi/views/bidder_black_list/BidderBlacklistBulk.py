from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.serializers.BidderBlacklistSerializer import BidderBlacklistIdsSerializer
from restapi.views.BaseBulkOperations import BaseBulkOperations


class BidderBlacklistBulk(BaseBulkOperations):
    model = BidderBlacklistIds
    serializer = BidderBlacklistIdsSerializer
