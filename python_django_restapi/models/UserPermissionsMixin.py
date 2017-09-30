# encoding: utf-8
"""Defines UserPermissionsMixin."""

from __future__ import unicode_literals

import hashlib

import six

from django.utils import lru_cache
from django.contrib.auth.models import Permission
from django.core.cache import cache

CACHE_TIME = 60

ANY, OWN = 'any', 'own'


def is_superuser(user):
    """Returns True if given user is superuser otherwise False."""
    return getattr(user, 'is_superuser', False)


def is_anonymous(obj):
    """Returns True if given user is anonymous otherwise False."""
    if callable(getattr(obj, 'is_anonymous', None)):
        return obj.is_anonymous()
    return False


@lru_cache.lru_cache()
def permission_for_any(model_name, action):
    """Returns prefix for permission that grants a given action on any entities of a given model.

    :param model_name: model name.
    :param action: action.
    :return: permission prefix.
    """
    return 'restapi.%s.%s.%s.' % (model_name, ANY, action)


@lru_cache.lru_cache()
def permission_for_own(model_name, action):
    """Returns prefix for permission that grants a given action on own entities of a given model.

    :param model_name: model name.
    :param action: action.
    :return: permission prefix.
    """
    return 'restapi.%s.%s.%s.' % (model_name, OWN, action)


class UserPermissionsMixin(object):
    """User permission mixin class."""

    def check_model_permission(self, model, action):
        """Checks if user has permissions to make given action on a given model.

        :param model: model class.
        :param action: can be one of create, read, update, delete.
        :returns: ANY/OWN/False
        """
        if is_superuser(self):
            return ANY

        model_name = model if isinstance(model, six.string_types) else model.get_perm_model_name()

        cache_key = 'restapi:%s:check_model_permission:%s:%s' % (self.pk, model_name, action)
        value = cache.get(cache_key)
        if value is None:
            permissions = self.get_all_permissions()
            if [x for x in permissions if x.startswith(permission_for_any(model_name, action))]:
                value = ANY
            elif [x for x in permissions if x.startswith(permission_for_own(model_name, action))]:
                value = OWN
            else:
                value = False
            cache.set(cache_key, value, CACHE_TIME)
        return value

    def check_instance_permission(self, instance, action):
        """Checks if user has permissions to make given action on a given instance.

        :param instance: instance.
        :param action: can be on of create, read, update, delete.
        """
        model = instance.__class__
        model_name = model.get_perm_model_name()

        if is_superuser(self):
            return ANY

        cache_key = 'restapi:%s:check_instance_permission:%s:%s:%s' % (self.pk, model_name, instance.pk, action)
        value = cache.get(cache_key)
        if value is None:
            value = False
            if self.check_model_permission(model=model, action=action):
                permissions = self.get_all_permissions()
                if [x for x in permissions if x.startswith(permission_for_any(model_name, action))]:
                    value = ANY
                elif [x for x in permissions if x.startswith(permission_for_own(model_name, action))]:
                    if instance.is_own():
                        value = OWN
            cache.set(cache_key, value, CACHE_TIME)
        return value

    def get_permitted_model_fields(self, model, action, fields):
        ''' Get a set of permitted fields for selected action: create, read, update, delete '''
        fields = set(fields)

        model_name = model if isinstance(model, six.string_types) else model.get_perm_model_name()

        if is_superuser(self):
            return fields

        fields_md5 = hashlib.md5(','.join(fields)).hexdigest()
        cache_key = 'restapi:%s:get_permitted_model_fields:%s:%s:%s' % (self.pk, model_name, fields_md5, action)
        value = cache.get(cache_key)
        if value is not None:
            return value

        permitted_fields = set()
        if self.check_model_permission(model=model, action=action):
            for ownership in {ANY, OWN}:
                perm_name = 'restapi.%s.%s.%s.' % (model_name, ownership, action)
                permitted_fields |= self._get_permitted_fields(perm_name, fields)

        cache.set(cache_key, permitted_fields, CACHE_TIME)
        return permitted_fields

    def get_permitted_instance_fields(self, instance, action, fields):
        """Get a set of permitted fields for selected action: create, read, update, delete"""
        fields = set(fields)

        model = instance.__class__
        model_name = model if isinstance(model, six.string_types) else model.get_perm_model_name()

        if is_superuser(self):
            return fields

        fields_md5 = hashlib.md5(','.join(fields)).hexdigest()
        cache_key = "restapi:%s:get_permitted_instance_fields:%s:%s:%s:%s" % (
            self.pk, model_name, instance.pk, fields_md5, action)
        value = cache.get(cache_key)
        if value is not None:
            return value

        permitted_fields = set()
        if self.check_instance_permission(instance=instance, action=action):
            # any
            permitted_fields_any = self._get_permitted_fields(permission_for_any(model_name, action), fields)

            # own
            permitted_fields_own = set()
            if instance.is_own():
                permitted_fields_own = self._get_permitted_fields(permission_for_own(model_name, action), fields)

            permitted_fields = permitted_fields_own | permitted_fields_any

        cache.set(cache_key, permitted_fields, CACHE_TIME)
        return permitted_fields

    def get_all_permissions(self):
        """Returns a set of all user permissions."""
        if is_anonymous(self):
            return set()

        cache_key = 'restapi:%s:get_all_permissions' % self.pk
        permissions = cache.get(cache_key)
        if permissions is not None:
            return permissions

        permissions = set('%s.%s' % (p.content_type.app_label, p.codename)
                          for p in self.user_permissions.select_related())
        user_groups_field = self._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        perms = Permission.objects.filter(**{user_groups_query: self})
        perms = perms.values_list('content_type__app_label', 'codename').order_by()
        permissions.update(set('%s.%s' % (ct, name) for ct, name in perms))

        cache.set(cache_key, permissions, CACHE_TIME)
        return permissions

    def _get_permitted_fields(self, perm_name, fields):
        """Returns a set of fields that are permitted for user."""
        all_permitted_fields = set()
        for perm in self.get_all_permissions():
            if perm.startswith(perm_name):
                fields_line = perm[len(perm_name):]
                permitted_fields = set()
                for field in fields_line.split(','):
                    if field:
                        if field == '*':
                            permitted_fields = fields
                        elif field[0] == '!':
                            field = field[1:]
                            if field in permitted_fields:
                                permitted_fields.remove(field)
                        else:
                            permitted_fields.add(field)
                all_permitted_fields |= permitted_fields
        return all_permitted_fields
