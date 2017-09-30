from django.conf import settings
import urllib
from urllib2 import Request, urlopen
import re
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from django.http import StreamingHttpResponse, HttpResponse
from datetime import datetime, timedelta

from restapi.models.Advertiser import Advertiser
from restapi.models.Campaign import Campaign
from restapi.models.base import PermissionDeniedException
from restapi.registry import REGISTRY


@permission_classes((permissions.IsAuthenticated,))
def device_id(request):
    # check permissions
    user = REGISTRY.get('user', None)
    if not bool(user.get_permitted_model_fields(model='tools', action='read', fields=['device_id'])):
        raise PermissionDeniedException()

    advertiser_id = request.GET.get('advertiser_id', '')
    advertiser = None
    if advertiser_id:
        qs = Advertiser.objects.filter(pk=advertiser_id)
        if qs.exists():
            advertiser = qs.first()
        else:
            advertiser_id = ''

    campaign_id = request.GET.get('campaign_id', '') if advertiser else ''
    if campaign_id:
        qs = advertiser.campaign_set.filter(campaign_id=campaign_id)
        if not qs.exists():
            campaign_id = ''

    params = {'type': request.GET.get('type', ''),
              'start': request.GET.get('start', ''),
              'end': request.GET.get('end', ''),
              'advertiser_id': advertiser_id,
              'campaign_id': campaign_id}

    if not params['start']:
        params['start'] = '2011-09-01'

    if not params['end']:
        end = datetime.now() + timedelta(days=1)
        params['end'] = end.strftime("%Y-%m-%d")

    for key in ['start','end']:
        params[key] = re.sub(r'-(\d)-', r'-0\1-', params[key])
        params[key] = re.sub(r'-(\d)$', r'-0\1', params[key])

    api_file = '2/download-device-ids.php'
    api_root = settings.STATS_API_DOMAIN + api_file + '?key=' + settings.STATS_API_KEY
    query_string = urllib.urlencode(params)
    api_for_sql_query = api_root + '&' + query_string
    request = Request(api_for_sql_query)
    response = HttpResponse(content_type='text/csv')
    try:
        api_response = urlopen(request)
        def stream_response_generator():
            while True:
                data = api_response.read(1024)
                if not data:
                    return
                yield data
        response = StreamingHttpResponse(stream_response_generator(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="device_id.csv"'
    # pylint: disable=bare-except
    except:
        response.write('Data invalid')
    return response
