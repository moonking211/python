from django.http import HttpResponse
from django.conf import settings
import mimetypes
from rest_framework import permissions
import urllib2
from rest_framework.decorators import permission_classes


@permission_classes((permissions.IsAuthenticated,))
def proxy_to(request, path, target_url):
    url = '%s%s?key=%s' % (target_url, path, settings.STATS_API_KEY)
    if request.META.has_key('QUERY_STRING'):
        url += '&' + request.META['QUERY_STRING']
    try:
        proxied_request = urllib2.urlopen(url)
        status_code = proxied_request.code
        mime_type = proxied_request.headers.typeheader or mimetypes.guess_type(url)
        content = proxied_request.read()
    except urllib2.HTTPError as error:
        response = HttpResponse(error.msg, status=error.code)
        response.content_type = 'text/plain'
    else:
        response = HttpResponse(content, status=status_code)
        response.content_type = mime_type
    return response
