from restapi.models.DiscretePricing import DiscretePricing
from restapi.models.DiscretePricing import DiscretePricingIds
from restapi.serializers.DiscretePricingSerializer import DiscretePricingSerializer
from restapi.serializers.DiscretePricingSerializer import DiscretePricingIdsSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class DiscretePricingDetail(BaseDetail):
    queryset = DiscretePricingIds.objects.all()
    serializer_class = DiscretePricingIdsSerializer

    def get(self, *args, **kwargs):
        self.serializer_class = DiscretePricingSerializer
        self.queryset = DiscretePricing.objects.all()
        return super(DiscretePricingDetail, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.serializer_class = DiscretePricingIdsSerializer
        self.queryset = DiscretePricingIds.objects.all()
        return super(DiscretePricingDetail, self).post(*args, **kwargs)
