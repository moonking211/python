from restapi.models.Campaign import Campaign
from restapi.serializers.CampaignSerializer import CampaignSerializer, TWInternalCampaignSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate

from django.http import QueryDict


class CampaignList(BaseListCreate):
    # List all campaigns, or create a new campaign.
    # queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    list_filter_fields = \
        ('status', 'advertiser_id', 'advertiser_id__agency_id__trading_desk_id', 'advertiser_id__agency_id', 'campaign_id')
    contains_filter_include_pk = True
    contains_filter_fields = ('campaign',)
    query_filter_fields = ('campaign', 'campaign_id')
    order_fields = ('campaign', '-campaign',
                    'campaign_id', '-campaign_id')

    @property
    def queryset(self):
        return Campaign.objects.filter(source_type=1).all()

    def get_queryset(self):
        params = self.request.query_params
        trading_desk_id = params.get('trading_desk_id')
        agency_id = params.get('agency_id')

        query_params = QueryDict('', mutable=True)
        query_params.update(params)

        if trading_desk_id is not None:
            query_params['advertiser_id__agency_id__trading_desk_id'] = trading_desk_id

        if agency_id is not None:
            query_params['advertiser_id__agency_id'] = agency_id

        self.query_params = query_params

        return super(CampaignList, self).get_queryset()


class TWCampaignList(CampaignList):
    serializer_class = TWInternalCampaignSerializer
    @property
    def queryset(self):
        return Campaign.objects.filter(source_type=2).all()