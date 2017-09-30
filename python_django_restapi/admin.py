# encoding: utf-8
"""Defines model admin for all models."""

from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes import models as content_types_models
from django.contrib.auth import models as auth_models
from django.contrib.auth import admin as auth_admin
from django.utils import translation

from restapi.models import User
from restapi.models import UserProfile


class UserAdmin(auth_admin.UserAdmin):
    """Model admin for User model."""
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (translation.ugettext_lazy('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (translation.ugettext_lazy('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                                                               'user_permissions')}),
        (translation.ugettext_lazy('Important dates'), {'fields': ('last_login',)}),
    )


admin.site.register(User, UserAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    """Model admin for UserProfile model."""
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_select_related = ('user',)


admin.site.register(UserProfile, UserProfileAdmin)


class PermissionAdmin(admin.ModelAdmin):
    """Model admin for Permission."""
    search_fields = ('name', 'codename')
    list_filter = ('content_type',)
    list_display = ('content_type', 'name', 'codename')


admin.site.register(auth_models.Permission, PermissionAdmin)


class ContentTypeAdmin(admin.ModelAdmin):
    """Model admin for ContentType."""
    search_fields = ('app_label', 'name')
    list_filter = ('app_label',)
    list_display = ('app_label', 'name')


admin.site.register(content_types_models.ContentType, ContentTypeAdmin)
