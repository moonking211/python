from restapi.models.BidderWhitelist import BidderWhitelist
from restapi.models.BidderWhitelist import BidderWhitelistIds
from restapi.serializers.BidderWhitelistSerializer import BidderWhitelistSerializer
from restapi.serializers.BidderWhitelistSerializer import BidderWhitelistIdsSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class BidderWhitelistDetail(BaseDetail):
    # Retrieve, update or delete a bidder_whitelist instance.
    # queryset = BidderWhitelistIds.objects.all()
    serializer_class = BidderWhitelistIdsSerializer

    def get(self, *args, **kwargs):
        self.serializer_class = BidderWhitelistSerializer
        self.queryset = BidderWhitelist.objects.all()
        return super(BidderWhitelistDetail, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.serializer_class = BidderWhitelistIdsSerializer
        self.queryset = BidderWhitelistIds.objects.all()
        return super(BidderWhitelistDetail, self).post(*args, **kwargs)
