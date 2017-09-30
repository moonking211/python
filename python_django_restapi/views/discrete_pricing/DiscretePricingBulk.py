from restapi.models.DiscretePricing import DiscretePricingIds
from restapi.serializers.DiscretePricingSerializer import DiscretePricingIdsSerializer
from restapi.views.BaseBulkOperations import BaseBulkOperations


class DiscretePricingBulk(BaseBulkOperations):
    model = DiscretePricingIds
    serializer = DiscretePricingIdsSerializer
