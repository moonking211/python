from restapi.models.MraidAdTemplate import MraidAdTemplate
from restapi.serializers.MraidAdTemplateSerializer import MraidAdTemplateSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class MraidAdTemplateDetail(BaseDetail):
    serializer_class = MraidAdTemplateSerializer

    @property
    def queryset(self):
        return MraidAdTemplate.objects.all()
