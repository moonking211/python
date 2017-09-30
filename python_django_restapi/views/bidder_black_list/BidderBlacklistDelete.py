from restapi.models.BidderBlacklist import BidderBlacklist
from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.views.BasePlasementDelete import BasePlasementDelete


class BidderBlacklistDelete(BasePlasementDelete):
    model = BidderBlacklist
    modelIds = BidderBlacklistIds
