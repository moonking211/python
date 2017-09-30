import json
import hashlib
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from restapi.models.choices import STATUS_ARCHIVED
from restapi.models.base import PermissionDeniedException
from restapi.registry import REGISTRY
from restapi.serializers.validators.BaseValidator import BaseValidator

CACHE_TIME = 3600


class BaseManager(models.Manager):
    MIN_CHAR_SEARCH_BY_NAME = 3

    def filter_by_list(self, params, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        for name in params.keys():
            args = {'%s__in' % name: params[name]}
            queryset = queryset.filter(**args)
        return queryset

    def search(self, value, queryset=None, exclude_archived=False):
        # pylint: disable=no-member
        model = self.model
        if value is not None and value != '' and model.search_args:
            kwargs = []
            for arg in model.search_args:
                # pylint: disable=protected-access
                if arg in model._meta.get_all_field_names():
                    # pylint: disable=protected-access
                    field = model._meta.get_field_by_name(arg)[0]
                    try:
                        field.to_python(value)
                    except ValidationError:
                        continue

                if len(value) < self.MIN_CHAR_SEARCH_BY_NAME and BaseValidator.is_digit(value):
                    kwargs.append({arg: value})
                    break

                kwargs.append({arg: value})
            filter_query = [Q(**kwarg) for kwarg in kwargs]
            if not filter_query:
                queryset = model.objects.none()
            else:
                queryset = self.filter(reduce(lambda q1, q2: q1 | q2, filter_query))
        if exclude_archived:
            queryset = self._exclude_archived(queryset)
        return queryset

    # pylint: disable=no-self-use
    def _exclude_archived(self, queryset):
        return queryset.exclude(status=STATUS_ARCHIVED)

    def get(self, *args, **kwargs):
        instance = super(BaseManager, self).get(*args, **kwargs)
        user = REGISTRY.get('user', None)
        # pylint: disable=attribute-defined-outside-init
        if self.model.permission_check and settings.SYSTEM_USER is False:
            if not user or user.is_anonymous():
                from restapi.models.User import User
                if self.model == User:
                    return instance
                raise ValueError('Unable resolve current user.')

            if not user.check_instance_permission(instance=instance, action='read'):
                raise PermissionDeniedException("user=%s; action=%s; model=%s; all_permissions=%s;" %
                                                (user.username,
                                                 'read',
                                                 self.model.__name__,
                                                 repr(user.get_all_permissions())))
        return instance

    def all(self, *args, **kwargs):
        queryset = super(BaseManager, self).all(*args, **kwargs)
        user = REGISTRY.get('user', None)
        if not user or user.is_anonymous():
            from restapi.models.User import User
            if self.model == User:
                return queryset
        if self.model.permission_check:
            queryset = self.filter_by_authorized_user(queryset)
        return queryset

    def filter(self, *args, **kwargs):
        queryset = super(BaseManager, self).filter(*args, **kwargs)
        if self.model.permission_check:
            queryset = self.filter_by_authorized_user(queryset)
        return queryset

    def get_queryset(self, *args, **kwargs):
        return super(BaseManager, self).get_queryset(*args, **kwargs)

    def filter_by_authorized_user(self, queryset):
        user = REGISTRY['user']
        model_perm = user.check_model_permission(model=self.model, action='read')
        if not model_perm:
            raise PermissionDeniedException('user=%s; action=%s; model=%s; all_permissions=%s;' % (
                user.username, 'read', self.model.get_perm_model_name(), repr(user.get_all_permissions())
            ))

        if model_perm == 'own':
            queryset = self.own(queryset)
        return queryset

    def raw(self, *args, **kwargs):
        return super(BaseManager, self).raw(*args, **kwargs)

    def own(self, queryset=None):
        return self.all() if queryset is None else queryset.all()

    def getCount(self, queryset=None, **kwargs):
        CACHE_KEY = self.getCountCacheKey(**kwargs)
        value = cache.get(CACHE_KEY) or 0
        return value

    def getCountCacheKey(self, **kwargs):
        if not self.checkCounterKey(**kwargs):
            assert self.checkCounterKey(**kwargs), "No counter key found in args"
        model_name = self.model.__name__
        kwargs_array = [(k, kwargs[k]) for k in sorted(kwargs.keys())]
        param = hashlib.md5(json.dumps(kwargs_array)).hexdigest()
        result = "restapi:model_count:%s:%s" % (model_name, param)
        return result

    def checkCounterKey(self, **kwargs):
        return False
