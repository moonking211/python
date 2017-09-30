from restapi.models.Ad import Ad
from restapi.serializers.AdSerializer import AdSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class AdList(BaseListCreate):
    # List all ads, or create a new ad.
    # queryset = Ad.objects.all()
    serializer_class = AdSerializer
    query_filter_fields = ('ad', 'ad_id')
    list_filter_fields = ('status', 'ad_group_id', 'ad', 'adx_status', 'a9_status', 'ad_id', 'size')
    order_fields = ('ad', '-ad',
                    'ad_id', '-ad_id',
                    'size', '-size',
                    'last_update', '-last_update',
                    'created_time', '-created_time',
                    'adx_status', '-adx_status',
                    'a9_status', '-a9_status',
                    'tag', '-tag')

    @property
    def queryset(self):
        return Ad.objects.all()

    def get_queryset(self):
        params = self.request.query_params
        queryset = super(AdList, self).get_queryset()
        order = params.get('order', None)
        advertiser_id = params.get('advertiser_id', None)
        campaign_id = params.get('campaign_id', None)
        entity_id = params.get('entity_id', None)

        if advertiser_id:
            queryset = queryset.filter(ad_group_id__campaign_id__advertiser_id__pk=advertiser_id)

        if campaign_id:
            queryset = queryset.filter(ad_group_id__campaign_id__pk=campaign_id)

        if entity_id:
            queryset = queryset.filter(ad_id=entity_id)

        if order == 'ad_type':
            queryset = queryset.extra(
                select={'ad_order': "FIELD(ad_type, 1, 4, 5, 6, 2, 3)"},
                order_by=['ad_order']
            )
        if order == '-ad_type':
            queryset = queryset.extra(
                select={'ad_order': "FIELD(ad_type, 3, 2, 6, 5, 4, 1)"},
                order_by=['ad_order']
            )
        return queryset
