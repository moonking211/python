from django.db import transaction
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework import views
from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign


class BasePlasementDelete(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    model = None
    modelIds = None
    FILTER_PARAMS = ('advertiser_id',
                     'campaign_id',
                     'ad_group_id',
                     'source_id',
                     'placement_type',
                     'placement_id',
                     'tag')

    def _model_filter(self, model, status, param):
        kfilter = {}
        if status == 'enabled':
            kfilter['status'] = 'enabled'
        elif status == 'enabled_paused':
            kfilter['status__in'] = ['enabled', 'paused']
        return list(model.objects.filter(**kfilter).values_list(param, flat=True))

    def post(self, request):
        data = request.DATA
        entity_status = data.get('entity_status')
        active_value = data.get('active', None)
        kfilter_param = {field: data.get(field, None) for field in self.FILTER_PARAMS}
        for k, v in kfilter_param.items():
            if not v:
                del kfilter_param[k]

        campaign_ids = self._model_filter(Campaign, entity_status, 'campaign_id')
        ad_group_ids = self._model_filter(AdGroup, entity_status, 'ad_group_id')
        result_queryset = self.model.objects.filter(campaign_id__in=[0] + campaign_ids,
                                                    ad_group_id__in=[0] + ad_group_ids)
        if active_value is not None:
            result_queryset = self.model.objects.filter_by_list({'active': [active_value]}, result_queryset)
        model_ids_list = list(result_queryset.filter(**kfilter_param).values_list('id', flat=True))

        with transaction.atomic():
            for instance in self.modelIds.objects.filter(id__in=model_ids_list):
                instance.delete()

        status = HTTP_200_OK
        return Response(status=status)
