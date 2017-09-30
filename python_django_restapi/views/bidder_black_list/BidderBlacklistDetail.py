from restapi.models.BidderBlacklist import BidderBlacklist
from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.serializers.BidderBlacklistSerializer import BidderBlacklistIdsSerializer
from restapi.serializers.BidderBlacklistSerializer import BidderBlacklistSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class BidderBlacklistDetail(BaseDetail):
    # Retrieve, update or delete a bidder_blacklist instance.
    # queryset = BidderBlacklistIds.objects.all()
    serializer_class = BidderBlacklistIdsSerializer

    def get(self, *args, **kwargs):
        self.serializer_class = BidderBlacklistSerializer
        self.queryset = BidderBlacklist.objects.all()
        return super(BidderBlacklistDetail, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.serializer_class = BidderBlacklistIdsSerializer
        self.queryset = BidderBlacklistIds.objects.all()
        return super(BidderBlacklistDetail, self).post(*args, **kwargs)
