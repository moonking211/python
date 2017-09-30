# encoding: utf-8

from __future__ import unicode_literals

from django import http
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import logout as auth_logout


def logout(request):
    if request.method != 'POST':
        return http.HttpResponseNotAllowed(permitted_methods=('POST',))

    auth_logout(request)

    return http.JsonResponse({'success': True}, status=200)
