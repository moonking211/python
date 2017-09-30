from rest_framework import serializers
from rest_framework import permissions
from rest_framework import views
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from restapi.models.AdGroup import AdGroup
from restapi.serializers.AdGroupSerializer import AdGroupSerializer


class AdGroupsChangeStatus(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    model = AdGroup
    serializer = AdGroupSerializer

    def post(self, request):
        data = request.DATA
        failed_object = {}
        success_object = {}
        status = HTTP_200_OK

        try:
            src_ad_group_ids = [long(x) for x in data['src_ad_group_ids']]
            new_status = str(data['new_status'])
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST

        src_ad_groups_qs = self.model.objects.filter(pk__in=src_ad_group_ids)

        count = 0
        for ad_group in src_ad_groups_qs:
            if ad_group.status == new_status:
                continue

            try:
                ad_group.status = new_status
                data_entry = ad_group.as_dict()
                serializer = self.serializer(data=data_entry,
                                             context={'request': request},
                                             instance=ad_group)
                serializer.is_valid(raise_exception=True)
                ad_group.save()
                count += 1

            except serializers.ValidationError as exception:
                error_entry = 'ad_group_id ' + str(data_entry.get('ad_group_id'))
                error_msg = exception.detail if hasattr(exception, 'detail') else exception.message
                failed_object[error_entry] = error_msg
                status = HTTP_400_BAD_REQUEST

        if count > 0:
            success_object[count] = 'Status was successfully changed to %s' % new_status

        return Response({'success': success_object, 'error': failed_object},
                        status=status,
                        content_type='application/json')
