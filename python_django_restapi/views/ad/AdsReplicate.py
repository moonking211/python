from django.db import transaction
from django.forms.models import model_to_dict
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authentication import SessionAuthentication

from restapi.models.Ad import Ad
from restapi.models.choices import STATUS_ENABLED, STATUS_PAUSED, STATUS_ARCHIVED
from restapi.serializers.AdSerializer import AdSerializer


class AdsReplicate(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    model = Ad
    serializer = AdSerializer

    def post(self, request):
        data = request.DATA
        created_ads = []

        try:
            src_ad_group_id = long(data['src_ad_group_id'])
            src_ad_ids = [long(x) for x in data['src_ad_ids']]
            src_ad_statues = [str(x) for x in data['src_ad_statuses']]
            dst_ad_group_ids = [long(x) for x in data['dst_ad_group_ids']]
            retain_ads_status = bool(data['retain_ads_status'])
            all_enabled_ads = bool(data['all_enabled_ads'])
            all_paused_ads = bool(data['all_paused_ads'])
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST
        else:
            with transaction.atomic():
                if 'all' in src_ad_statues: src_ad_statues = [STATUS_ENABLED, STATUS_PAUSED, STATUS_ARCHIVED]
                # If src_ad_ids is single element list with value of -1,
                # then it replicates all ads of the group specified by the src_ad_group_id.
                if len(src_ad_ids) == 1 and src_ad_ids[0] == -1:
                    src_ads = self.model.objects.filter(ad_group_id_id=src_ad_group_id, status__in=src_ad_statues)
                else:
                    src_ads = self.model.objects.filter(pk__in=src_ad_ids, status__in=src_ad_statues)

                src_ads_list = list(src_ads)
                for dst_ad_group_id in dst_ad_group_ids:
                    # pylint: disable=invalid-name
                    for ad in src_ads_list:

                        m = ad.make_copy()
                        m.ad_group_id_id = dst_ad_group_id

                        if retain_ads_status:
                            m.status = ad.status

                        elif all_enabled_ads:
                            m.status = STATUS_ENABLED

                        elif all_paused_ads:
                            m.status = STATUS_PAUSED

                        serializer = self.serializer(data=model_to_dict(m), context={'request': request}, instance=m)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                        created_ads.append(m.pk)

            status = HTTP_200_OK
        return Response(created_ads, status=status)
