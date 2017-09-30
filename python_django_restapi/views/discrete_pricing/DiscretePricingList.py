from django.db.models import Q
from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign
from restapi.models.DiscretePricing import DiscretePricing
from restapi.models.DiscretePricing import DiscretePricingIds
from restapi.serializers.DiscretePricingSerializer import DiscretePricingSerializer
from restapi.serializers.DiscretePricingSerializer import DiscretePricingIdsSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class DiscretePricingList(BaseListCreate):
    # queryset = DiscretePricingIds.objects.all()
    # pylint: disable=no-member
    serializer_class = DiscretePricingSerializer
    list_filter_fields = ('placement_id',
                          'source_id',
                          'placement_type',
                          'campaign_id',
                          'advertiser_id',
                          'ad_group_id',
                          'size')
#    list_filter_prepare = (('active', lambda x: True if x.lower() == 'true' else False),)
    contains_filter_fields = ('tag', )
    order_fields = ('ad_group', '-ad_group',
                    'campaign', '-campaign',
                    'size', '-size',
                    'source_id', '-source_id',
                    'placement_id', '-placement_id',
                    'tag', '-tag',
                    'created_at', '-created_at',
                    'rev_value', '-rev_value',
                    'last_update', '-last_update')

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            self.serializer_class = DiscretePricingSerializer
            self.queryset = DiscretePricing.objects.all()
        elif request.method == 'POST':
            self.serializer_class = DiscretePricingIdsSerializer
            self.queryset = DiscretePricingIds.objects.all()
        else:
            raise Exception("Unsupported method {}".format(request.method))

        return super(DiscretePricingList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        params = self.request.query_params
        queryset = super(DiscretePricingList, self).get_queryset()
        entity_status = params.get('entity_status', None)
        if entity_status == 'enabled':
            campaign_ids = list(Campaign.objects.filter(status='enabled').values_list('campaign_id', flat=True))
            ad_group_ids = list(AdGroup.objects.filter(status='enabled').values_list('ad_group_id', flat=True))
            queryset = queryset.filter(campaign_id__in=[0] + campaign_ids,
                                       ad_group_id__in=[0] + ad_group_ids)
        if entity_status == 'enabled_paused':
            campaign_ids = list(Campaign.objects.filter(status__in=['enabled', 'paused']).values_list('campaign_id', flat=True))
            ad_group_ids = list(AdGroup.objects.filter(status__in=['enabled', 'paused']).values_list('ad_group_id', flat=True))
            queryset = queryset.filter(campaign_id__in=[0] + campaign_ids,
                                       ad_group_id__in=[0] + ad_group_ids)
        return queryset

