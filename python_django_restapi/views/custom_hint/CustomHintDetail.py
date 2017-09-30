from restapi.models.CustomHint import CustomHint
from restapi.models.CustomHint import CustomHintIds
from restapi.serializers.CustomHintSerializer import CustomHintSerializer
from restapi.serializers.CustomHintSerializer import CustomHintIdsSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class CustomHintDetail(BaseDetail):
    # queryset = CustomHintIds.objects.all()
    serializer_class = CustomHintIdsSerializer

    def get(self, *args, **kwargs):
        self.serializer_class = CustomHintSerializer
        self.queryset = CustomHint
        return super(CustomHintDetail, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.serializer_class = CustomHintIdsSerializer
        self.queryset = CustomHintIds.objects.all()
        return super(CustomHintDetail, self).post(*args, **kwargs)
