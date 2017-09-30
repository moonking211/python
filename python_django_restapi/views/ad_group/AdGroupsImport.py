from rest_framework import permissions
from rest_framework import views
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authentication import SessionAuthentication

from restapi.models.AdGroup import AdGroup
from restapi.serializers.AdGroupSerializer import AdGroupSerializer


class AdGroupsImport(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    # pylint: disable=no-self-use
    def post(self, request, campaign_id):
        if 'data' not in request.DATA:
            return Response('', status=HTTP_400_BAD_REQUEST)
        data = request.DATA['data']

        result = []
        failed_data = []

        added = 0
        updated = 0
        failed = 0

        for data_entry in data:
            data_entry['campaign_id'] = campaign_id
            name = data_entry.get('ad_group', None)
            try:
                instance = AdGroup.objects.get(ad_group=name, campaign_id_id=campaign_id)
            except AdGroup.DoesNotExist:
                instance = None

            serializer = AdGroupSerializer(data=data_entry, context={'request': request}, instance=instance)
            errors = {}
            try:
                valid = serializer.is_valid(raise_exception=False)
                if valid:
                    serializer.save()
                    if instance:
                        updated += 1
                    else:
                        added += 1
                else:
                    errors = serializer._errors
            except Exception as exception:
                msg = exception.detail if hasattr(exception, 'detail') else exception.message
                errors = {'non_field_error': msg}

            if errors:
                data_entry['validations'] = errors
                del data_entry['campaign_id']
                failed_data.append(data_entry)
                failed += 1

        data = {'counters': {'added': added,
                             'updated': updated,
                             'failed': failed},
                'data': failed_data}
        status = HTTP_200_OK
        return Response(data, status=status)
