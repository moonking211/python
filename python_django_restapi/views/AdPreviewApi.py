from datetime import date, datetime, timedelta
from django.conf import settings

from django.utils import timezone
from restapi.time_shifting import PacificTimeShift

from rest_framework import views
from rest_framework.response import Response
from restapi.models.Ad import Ad
from restapi.models.AdPreview import AdPreview

class AdPreviewApi(views.APIView):
    # pylint: disable=no-self-use
    def get(self, request):
        method = request.method
        source_id = request.GET.get('source_id', '')
        ad_id = request.GET.get('ad_id', '')
        placement_id = request.GET.get('placement_id', '')
        device_id = request.GET.get('device_id', '').lower()
        data = {}
        valid_request = True

        SUPPORTED_SOURCES = {
            "22" : True,  # MoPub
            "4"  : True,  # AdX
            "30" : True,  # Inneractive
            "19" : True,  # Millennial Media
        }

        if not source_id:
            valid_request = False
            data['error'] = True
            data['message'] = "Missing Source ID"

        if not ad_id:
            valid_request = False
            data['error'] = True
            data['message'] = "Missing Ad ID"

        if not ad_id.isdigit():
            valid_request = False
            data['error'] = True
            data['message'] = "Invalid Ad ID"

        if not placement_id:
            valid_request = False
            data['error'] = True
            data['message'] = "Missing Placement ID"

        if not device_id:
            valid_request = False
            data['error'] = True
            data['message'] = "Missing Device ID"

        if source_id not in SUPPORTED_SOURCES:
            valid_request = False
            data['error'] = True
            data['message'] = "Invalid Source ID"

        if device_id.lower() not in dict((k.lower(), v) for k, v in settings.AD_PREVIEW_WHITELISTED_TEST_DEVICES.iteritems()):
            if placement_id.lower() in dict((k.lower(), v) for k, v in settings.AD_PREVIEW_WHITELISTED_PLACEMENT_IDS.iteritems()):
                valid_request = True
            else:
                valid_request = False
                data['error'] = True
                data['message'] = "Test Device needs to be whitelisted when setting custom Placement ID. Please contact engineering."

        device_id = device_id.lower()

        if valid_request:
            ad = Ad.objects_raw.filter(ad_id=ad_id).first()

            if ad is not None:
                ad_group = ad.ad_group_id
                campaign = ad.ad_group_id.campaign_id
                ad_group_status = ad_group.status
                campaign_status = campaign.status
                status = "enabled"
                if ad.status != "enabled" or ad_group_status != "enabled" or campaign_status != "enabled":
                    status = "paused"
                try:
                    ad_preview = AdPreview.objects_raw.get(placement_id=placement_id, device_id=device_id, source_id=source_id)
                    ad_preview.ad_id = ad
                except AdPreview.DoesNotExist:
                    ad_preview = AdPreview(ad_id=ad, placement_id=placement_id, device_id=device_id, source_id=source_id)

                now = datetime.now()
                ad_preview.last_update = now + timedelta(hours=PacificTimeShift.get(now))
                ad_preview.save_raw();
                data = {
                    "error": False,
                    "ad":{
                        "size": str(ad.size),
                        "name": str(ad.ad),
                        "type": str(ad.ad_type),
                        "ad_group": str(ad_group),
                        "campaign": str(campaign),
                    },
                    "status": str(status),
                    "source_id": source_id,
                    "device_id": device_id,
                    "placement_id": placement_id,
                    "last_update": ad_preview.last_update,
                }
            else:
                data['error'] = True
                data['message'] = "Ad "+ str(ad_id) + " not found"

        response = Response(data)
        return response
