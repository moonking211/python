from django.forms.models import model_to_dict

from rest_framework import permissions
from rest_framework import views
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authentication import SessionAuthentication

from restapi.models.Ad import Ad
from restapi.serializers.AdSerializer import AdSerializer


class AdsChangeStatus(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    model = Ad
    serializer = AdSerializer

    def post(self, request):
        data = request.DATA
        failed_object = {}
        success_object = {}
        status = HTTP_200_OK

        src_ad_group_id = 0
        src_ad_ids = []
        src_ad_statues = []
        new_status = []
        try:
            src_ad_group_id = long(data['src_ad_group_id'])
            src_ad_ids = [long(x) for x in data['src_ad_ids']]
            src_ad_statues = [str(x) for x in data['src_ad_statuses']]
            new_status = str(data['new_status'])
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST

        # If src_ad_ids is single element list with value of -1,
        #  then it replicates all ads of the group specified by the src_ad_group_id.
        update_all_ad_in_src_group = len(src_ad_ids) == 1 and src_ad_ids[0] == -1
        if update_all_ad_in_src_group:
            src_ads = self.model.objects.filter(ad_group_id_id=src_ad_group_id, status__in=src_ad_statues)
        else:
            src_ads = self.model.objects.filter(pk__in=src_ad_ids, status__in=src_ad_statues)

        count = 0
        for ad_entry in src_ads:
            if ad_entry.status == new_status:
                continue

            ad_entry.status = new_status
            try:
                data_entry = model_to_dict(ad_entry)
                serializer = self.serializer(data=data_entry,
                                             context={'request': request},
                                             instance=ad_entry)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                count += 1

            except serializers.ValidationError as exception:
                error_entry = 'Ad id ' + str(data_entry.get('ad_id'))
                error_msg = exception.detail if hasattr(exception, 'detail') else exception.message
                failed_object[error_entry] = error_msg
                status = HTTP_400_BAD_REQUEST

        if count > 0:
            success_object[count] = 'Status was successfully changed to %s' % new_status

        return Response({'succes': success_object, 'error': failed_object},
                        status=status,
                        content_type='application/json')
