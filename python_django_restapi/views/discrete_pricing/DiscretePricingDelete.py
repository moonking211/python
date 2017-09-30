from restapi.models.DiscretePricing import DiscretePricing
from restapi.models.DiscretePricing import DiscretePricingIds
from restapi.views.BasePlasementDelete import BasePlasementDelete


class DiscretePricingDelete(BasePlasementDelete):
    model = DiscretePricing
    modelIds = DiscretePricingIds
