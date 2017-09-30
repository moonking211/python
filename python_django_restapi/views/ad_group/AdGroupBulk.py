from restapi.models.AdGroup import AdGroup
from restapi.views.BaseBulkOperations import BaseBulkOperations
from restapi.serializers.AdGroupSerializer import AdGroupSerializer


class AdGroupBulk(BaseBulkOperations):
    model = AdGroup
    serializer = AdGroupSerializer
