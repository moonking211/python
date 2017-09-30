from copy import copy

from rest_framework import serializers
from rest_framework import views
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from restapi.models.AdGroup import AdGroup
from restapi.serializers.AdGroupSerializer import AdGroupSerializer


class RevmapsUpdateAll(views.APIView):

    #pylint: disable=no-self-use
    def post(self, request):
        post_data = copy(request.DATA)
        failed_object = {}
        success_object = {}
        status = HTTP_200_OK

        src_ad_group_ids = post_data.pop('ad_group_ids', [])
        count = 0
        for ad_group_id in src_ad_group_ids:
            try:
                ad_group = AdGroup.objects.get(pk=ad_group_id)
                data = ad_group.as_dict()

                for f in post_data:
                    if f in ['rev_value', 'rev_type', 'opt_value', 'opt_type']:
                        data['revmap_%s' % f] = post_data[f]

                serializer = AdGroupSerializer(data=data, context={'request': request}, instance=ad_group)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                count += 1

            except serializers.ValidationError as exception:
                error_entry = 'ad_group_id ' + str(ad_group_id)
                error_msg = exception.detail if hasattr(exception, 'detail') else exception.message
                failed_object[error_entry] = error_msg
                status = HTTP_400_BAD_REQUEST

        if count > 0:
            success_object[count] = 'Rates was successfully changed for chosen ad groups'

        return Response({'success': success_object, 'error': failed_object},
                        status=status,
                        content_type='application/json')
