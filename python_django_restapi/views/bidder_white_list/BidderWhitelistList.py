from restapi.models.AdGroup import AdGroup
from restapi.models.BidderWhitelist import BidderWhitelist
from restapi.models.BidderWhitelist import BidderWhitelistIds
from restapi.models.Campaign import Campaign
from restapi.serializers.BidderWhitelistSerializer import BidderWhitelistSerializer
from restapi.serializers.BidderWhitelistSerializer import BidderWhitelistIdsSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class BidderWhitelistList(BaseListCreate):
    # List all bidder_whitelist, or create a new ad group.
    # pylint: disable=no-member
    # queryset = BidderWhitelist.objects.all()
    serializer_class = BidderWhitelistSerializer
    list_filter_fields = ('source_id',
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
            self.serializer_class = BidderWhitelistSerializer
            self.queryset = BidderWhitelist.objects.all()
        elif request.method == 'POST':
            self.serializer_class = BidderWhitelistIdsSerializer
            self.queryset = BidderWhitelistIds.objects.all()
        else:
            raise Exception("Unsupported method {}".format(request.method))

        return super(BidderWhitelistList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        params = self.request.query_params
        queryset = super(BidderWhitelistList, self).get_queryset()
        entity_status = params.get('entity_status', None)
        if entity_status == 'enabled':
            campaign_ids = list(Campaign.objects.filter(status='enabled').values_list('campaign_id', flat=True))
            ad_group_ids = list(AdGroup.objects.filter(status='enabled').values_list('ad_group_id', flat=True))
            queryset = queryset.filter(campaign_id__in=[0] + campaign_ids,
                                       ad_group_id__in=[0] + ad_group_ids)
        elif entity_status == 'enabled_paused':
            campaign_ids = list(Campaign.objects.filter(status__in=['enabled', 'paused'])
                                .values_list('campaign_id', flat=True))
            ad_group_ids = list(AdGroup.objects.filter(status__in=['enabled', 'paused'])
                                .values_list('ad_group_id', flat=True))
            queryset = queryset.filter(campaign_id__in=[0] + campaign_ids,
                                       ad_group_id__in=[0] + ad_group_ids)
        return queryset
