from restapi.models.AdGroup import AdGroup
from restapi.models.BidderBlacklist import BidderBlacklist
from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.models.Campaign import Campaign
from restapi.serializers.BidderBlacklistSerializer import BidderBlacklistSerializer
from restapi.serializers.BidderBlacklistSerializer import BidderBlacklistIdsSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class BidderBlacklistList(BaseListCreate):
    # List all bidder_blacklist, or create a new ad group.
    # pylint: disable=no-member
    # queryset = BidderBlacklist.objects.all()
    serializer_class = BidderBlacklistSerializer
    list_filter_fields = ('status',
                          'source_id',
                          'campaign_id',
                          'ad_group_id',
                          'placement_id',
                          'placement_type',
                          'advertiser_id')
    contains_filter_fields = ('tag',)
    order_fields = ('size', '-size',
                    'source_id', '-source_id',
                    'placement_id', '-placement_id',
                    'campaign', '-campaign',
                    'ad_group', '-ad_group',
                    'tag', '-tag',
                    'last_update', '-last_update')

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            self.serializer_class = BidderBlacklistSerializer
            self.queryset = BidderBlacklist.objects.all()
        elif request.method == 'POST':
            self.serializer_class = BidderBlacklistIdsSerializer
            self.queryset = BidderBlacklistIds.objects.all()
        else:
            raise Exception("Unsupported method {}".format(request.method))

        return super(BidderBlacklistList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        params = self.request.query_params
        queryset = super(BidderBlacklistList, self).get_queryset()
        entity_status = params.get('entity_status', None)
        if entity_status == 'enabled':
            campaign_ids = list(Campaign.objects.filter(status='enabled').values_list('campaign_id', flat=True))
            ad_group_ids = list(AdGroup.objects.filter(status='enabled').values_list('ad_group_id', flat=True))
            queryset = queryset.filter(campaign_id__in=[0] + campaign_ids,
                                       ad_group_id__in=[0] + ad_group_ids)
        elif entity_status == 'enabled_paused':
            campaign_ids = list(
                Campaign.objects.filter(status__in=['enabled', 'paused']).values_list('campaign_id', flat=True))
            ad_group_ids = list(
                AdGroup.objects.filter(status__in=['enabled', 'paused']).values_list('ad_group_id', flat=True))
            queryset = queryset.filter(campaign_id__in=[0] + campaign_ids,
                                       ad_group_id__in=[0] + ad_group_ids)
        return queryset
