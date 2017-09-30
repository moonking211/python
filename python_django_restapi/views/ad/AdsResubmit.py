from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions

from restapi.models.choices import AD_STATUS_DISAPPROVED, AD_STATUS_NEW
from restapi.models.Ad import Ad
from restapi.models.base import PermissionDeniedException
from restapi.registry import REGISTRY


class AdsResubmit(APIView):
    authentication_classes = (SessionAuthentication,)
    no_ads_found_msg = 'No ads were found by sended ids'
    model = Ad

    def post(self, request):
        data = request.DATA
        result = None

        # check permissions
        user = REGISTRY.get('user', None)
        if not bool(user.get_permitted_model_fields(model='tools', action='read', fields=['resubmission'])):
            raise PermissionDeniedException()

        try:
            src_ad_ids = [long(x) for x in data['src_ad_ids']]
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST
        else:
            src_ads = self.model.objects.filter(pk__in=src_ad_ids)
            if src_ads.exists():
                ad_adx_new = []
                for ad_entry in src_ads:
                    if ad_entry.adx_status == AD_STATUS_DISAPPROVED:
                        ad_entry.adx_status = AD_STATUS_NEW
                        ad_entry.save()

                        ad_adx_new.append(ad_entry.pk)

                status = HTTP_200_OK
                result = {'items': ad_adx_new}
            else:
                status = HTTP_400_BAD_REQUEST
                result = self.no_ads_found_msg

        return Response(data=result, status=status)
