from restapi.models.AdGroup import AdGroup
from restapi.models.choices import AD_GROUP_TYPE_CHOICES
from restapi.serializers.AdGroupSerializer import AdGroupSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate

AD_GROUP_TYPE_VALUES = [choice[0] for choice in AD_GROUP_TYPE_CHOICES]

class AdGroupList(BaseListCreate):
    # List all ad groups, or create a new ad group.
    #queryset = AdGroup.objects.all()
    serializer_class = AdGroupSerializer
    list_filter_fields = ('pk', 'ad_group_id', 'ad_group', 'ad_group_type', 'status', 'campaign_id',)
    query_filter_fields = ('ad_group', 'ad_group_id')
    order_fields = ('ad_group', '-ad_group',
                    'ad_group_id', '-ad_group_id')
    specific_order_field = (('ad_group_type', lambda value: AD_GROUP_TYPE_VALUES.index(value.ad_group_type)),
                            ('-ad_group_type', lambda value: -AD_GROUP_TYPE_VALUES.index(value.ad_group_type)))

    @property
    def queryset(self):
        return AdGroup.objects.all()

    def get(self, *args, **kwargs):
        params = self.request.query_params
        ad_group_id = params.get('ad_group_id')
        if ad_group_id:
            ids = []
            for pk in ad_group_id.split(','):
                try:
                    int(pk)
                    ids.append(pk)
                except ValueError:
                    pass
            params._mutable = True
            params.update({'ad_group_id': ','.join(ids) if ids else '0'})
            params._mutable = False
        return super(AdGroupList, self).get(*args, **kwargs)
