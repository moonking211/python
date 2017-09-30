from restapi.models.Campaign import Campaign
from restapi.views.BaseBulkOperations import BaseBulkOperations
from restapi.serializers.CampaignSerializer import CampaignSerializer


class CampaignBulk(BaseBulkOperations):
    model = Campaign
    serializer = CampaignSerializer
