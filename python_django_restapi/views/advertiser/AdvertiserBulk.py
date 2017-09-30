from restapi.models.Advertiser import Advertiser
from restapi.views.BaseBulkOperations import BaseBulkOperations
from restapi.serializers.AdvertiserSerializer import AdvertiserSerializer


class AdvertiserBulk(BaseBulkOperations):
    model = Advertiser
    serializer = AdvertiserSerializer
