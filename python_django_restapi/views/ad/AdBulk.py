from restapi.models.Ad import Ad
from restapi.views.BaseBulkOperations import BaseBulkOperations
from restapi.serializers.AdSerializer import AdSerializer


class AdBulk(BaseBulkOperations):
    model = Ad
    serializer = AdSerializer
