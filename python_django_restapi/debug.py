import logging

logger = logging.getLogger('debug')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    else:
        return request.META.get('REMOTE_ADDR')


def extra(request=None):
    user = '<unknown>'
    ip = '<unknown>'
    url = '<unknown>'
    if request:
        if hasattr(request, 'user'):
            user = request.user
        ip = get_client_ip(request)
        url = request.build_absolute_uri()

    return {'user': user, 'ip': ip, 'url': url}
