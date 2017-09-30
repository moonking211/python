# encoding: utf-8

from __future__ import unicode_literals

import json

from django import http
from django.contrib.auth import login as auth_login
from django.contrib.auth import forms

from django.views.decorators import cache
from django.views.decorators import csrf
from django.views.decorators import debug


@debug.sensitive_post_parameters()
@csrf.csrf_protect
@cache.never_cache
def login(request):
    if request.method != 'POST':
        return http.HttpResponseNotAllowed(('POST',))

    data = None
    if request.POST:
        data = request.POST
    elif 'application/json' in request.META.get('CONTENT_TYPE', '').split(';'):
        try:
            data = json.loads(request.body)
        except (ValueError, TypeError):
            pass
    if data is None:
        return http.JsonResponse({'success': False}, status=406)  # Not Acceptable

    form = forms.AuthenticationForm(request, data=data)
    if not form.is_valid():
        return http.JsonResponse({'success': False, 'error': dict(form.errors)}, status=400)  # Bad Request

    auth_login(request, form.get_user())

    return http.JsonResponse({'success': True})
