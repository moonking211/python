from django.db import models

from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign
from restapi.models.CustomHint import CustomHint
from restapi.models.CustomHint import CustomHintIds
from restapi.serializers.CustomHintSerializer import CustomHintSerializer
from restapi.serializers.CustomHintSerializer import CustomHintIdsSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class CustomHintList(BaseListCreate):
    # pylint: disable=no-member
    # queryset = CustomHint.objects.all()
    serializer_class = CustomHintSerializer
    list_filter_fields = ('active',
                          'placement_id',
                          'source_id',
                          'placement_type',
                          'campaign_id',
                          'advertiser_id',
                          'ad_group_id',
                          'ad_id',
                          'size')
    list_filter_prepare = (('active', lambda x: True if x.lower() == 'true' else False),)
    contains_filter_fields = ('tag',)
    order_fields = ('ad_group', '-ad_group',
                    'campaign', '-campaign',
                    'size', '-size',
                    'source_id', '-source_id',
                    'placement_id', '-placement_id',
                    'ad', '-ad',
                    'inflator_type', '-inflator_type',
                    'inflator', '-inflator',
                    'start_date', '-start_date',
                    'end_date', '-end_date',
                    'tag', '-tag',
                    'last_update', '-last_update',
                    'max_frequency', '-max_frequency',
                    'frequency_interval', '-frequency_interval')

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            self.serializer_class = CustomHintSerializer
            self.queryset = CustomHint.objects.all()
        elif request.method == 'POST':
            self.serializer_class = CustomHintIdsSerializer
            self.queryset = CustomHintIds.objects.all()
        else:
            raise Exception("Unsupported method {}".format(request.method))

        return super(CustomHintList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        params = self.request.query_params
        queryset = super(CustomHintList, self).get_queryset()
        entity_status = params.get('entity_status', None)

        status = ('enabled', 'paused') if entity_status == 'enabled_paused' else ('enabled',)
        if params.get('campaign_id', None) == '0' or params.get('ad_group_id', None) == '0':
            campaign_ids_query = Campaign.objects.filter(status__in=status).values('campaign_id')
            ad_group_ids_query = AdGroup.objects.filter(status__in=status).values('ad_group_id')
            queryset = queryset.filter(
                models.Q(campaign_id=0) |
                models.Q(campaign_id__in=campaign_ids_query)).filter(models.Q(ad_group_id=0) |
                models.Q(ad_group_id__in=ad_group_ids_query))
        else:
            queryset = queryset.filter(
                models.Q(campaign_id__status__isnull=True) | models.Q(campaign_id__status__in=status)
            ).filter(
                models.Q(ad_group_id__status__isnull=True) | models.Q(ad_group_id__status__in=status)
            )
        return queryset
