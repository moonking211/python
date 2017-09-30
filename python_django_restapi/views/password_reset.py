# encoding: utf-8

from __future__ import unicode_literals

import json

from django import http
from django.utils import http as http_utils
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import forms
from django.contrib.auth import tokens
from django.views.decorators import debug
from django.views.decorators import cache
from django.views.decorators import csrf

from rest_framework import status


@csrf.csrf_protect
def password_reset(request, email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=forms.PasswordResetForm, token_generator=tokens.default_token_generator,
                   from_email=settings.NO_REPLY_EMAIL, html_email_template_name=None):
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
        return http.HttpResponseBadRequest({'success': False}, status=406)  # Not Acceptable

    form = password_reset_form(data)
    if not form.is_valid():
        return http.JsonResponse({'success': False, 'error': dict(form.errors)}, status=status.HTTP_400_BAD_REQUEST)
    form.save(**{
        'domain_override': getattr(settings, 'DOMAIN', None),
        'use_https': request.is_secure(),
        'token_generator': token_generator,
        'from_email': from_email,
        'email_template_name': email_template_name,
        'subject_template_name': subject_template_name,
        'request': request,
        'html_email_template_name': html_email_template_name,
    })
    return http.JsonResponse({'success': True})


@debug.sensitive_post_parameters()
@cache.never_cache
def password_reset_confirm(request, uidb64=None, token=None, token_generator=tokens.default_token_generator,
                           set_password_form=forms.SetPasswordForm):
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
        return http.HttpResponseBadRequest({'success': False}, status=406)  # Not Acceptable

    UserModel = auth.get_user_model()
    try:
        user = UserModel._default_manager.get(pk=http_utils.urlsafe_base64_decode(uidb64))
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if not user or not token_generator.check_token(user, token):
        return http.JsonResponse({'success': False}, status=status.HTTP_404_NOT_FOUND)

    form = set_password_form(user, data=data)
    if not form.is_valid():
        return http.JsonResponse({'success': False, 'error': dict(form.errors)}, status=status.HTTP_400_BAD_REQUEST)
    form.save()
    return http.JsonResponse({'success': True})
