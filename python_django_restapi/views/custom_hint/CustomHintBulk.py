from restapi.models.CustomHint import CustomHintIds
from restapi.serializers.CustomHintSerializer import CustomHintIdsSerializer
from restapi.views.BaseBulkOperations import BaseBulkOperations


class CustomHintBulk(BaseBulkOperations):
    model = CustomHintIds
    serializer = CustomHintIdsSerializer
