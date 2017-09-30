from restapi.models.BidderWhitelist import BidderWhitelist
from restapi.models.BidderWhitelist import BidderWhitelistIds
from restapi.views.BasePlasementDelete import BasePlasementDelete


class BidderWhitelistDelete(BasePlasementDelete):
    model = BidderWhitelist
    modelIds = BidderWhitelistIds
