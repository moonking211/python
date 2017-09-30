from restapi.models.Campaign import Campaign
from restapi.serializers.CampaignSerializer import CampaignSerializer, TWInternalCampaignSerializer
from restapi.views.base_view.BaseDetail import BaseDetail

class CampaignDetail(BaseDetail):
    # Retrieve, update or delete a campaign instance.
#    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    @property
    def queryset(self):
        return Campaign.objects.filter().all()


class TWCampaignDetail(BaseDetail):
    serializer_class = TWInternalCampaignSerializer
    model = Campaign
    @property
    def queryset(self):
        return Campaign.objects.filter(source_type=2).all()