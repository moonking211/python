from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import six

from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict
import json
from pytz import timezone
from dateutil.parser import parse
from rest_framework.exceptions import APIException
from restapi.models.choices import STATUS_PAUSED
from restapi.registry import REGISTRY
from restapi.time_shifting import PacificTimeShift
from dateutil.tz import tzutc
from restapi.models.fields import JSONField, DateTimeField
from copy import deepcopy
from rest_framework import status
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

TZ = timezone(settings.TIME_ZONE)


class ReadOnlyModelWriteException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Access forbidden - Read only model')

    def __init__(self, detail=None):
        super(ReadOnlyModelWriteException, self).__init__(detail if detail is not None else self.default_detail)


class PermissionDeniedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Access forbidden - Permission denied exception')

    def __init__(self, detail=None):
        super(PermissionDeniedException, self).__init__(detail if detail is not None else self.default_detail)


def dict_as_json(data):
    assert isinstance(data, dict)
    values = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            if value.year <= 1000:
                value = '1000-01-01 00:00:00'
            elif value.year >= 9000:
                value = '9999-12-31 23:59:59'
            else:
                if not value.tzinfo:
                    value = TZ.localize(value)
                value = value.astimezone(tzutc()) + timedelta(hours=PacificTimeShift.get(value))
                value = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, date):
            value = value.strftime("%Y-%m-%d")
        elif isinstance(value, Decimal):
            value = float(data[key])
        values[key] = value
    return json.dumps(values)


class BaseModel(models.Model):
    search_args = ()

    permission_check = False
    actions = []

    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args, **kwargs)
        self.fix_datetimes()

    @classmethod
    def get_perm_model_name(cls):
        return cls.__name__.lower()

    def is_own(self):
        if self.pk is None:
            return True
        return bool(self.__class__.objects.filter(pk=self.pk))

    def fix_datetimes(self):
        model_fields = self._meta.fields
        datetime_fields = [f for f in model_fields if isinstance(f, models.DateTimeField)]
        for field in datetime_fields:
            value = getattr(self, field.name)
            if value:
                if isinstance(value, six.string_types):
                    new_value = parse(value)
                    setattr(self, field.name, new_value)
                elif not value.tzinfo:
                    new_value = TZ.localize(value)
                    setattr(self, field.name, new_value)
                elif str(value.tzinfo) == "UTC":
                    if value.year >= 9000:
                        value = value.replace(year=9000)
                    new_value = value.astimezone(tzutc()) - timedelta(
                        hours=PacificTimeShift.get(value.replace(tzinfo=timezone(settings.TIME_ZONE))))
                    setattr(self, field.name, new_value)

    def as_dict(self):
        self_copy = deepcopy(self)
        data = None
        for x in self_copy._meta.concrete_fields:
            if isinstance(x, DateTimeField) and not getattr(x, 'editable'):
                setattr(x, 'editable', True)
        data = model_to_dict(self_copy)
        for key, value in data.items():
            field = self_copy._meta.get_field_by_name(key)[0]
            if isinstance(field, JSONField):
                data[key] = json.dumps(value)
        return data

    def save_raw(self, *args, **kwargs):
        self.fix_datetimes()
        return super(BaseModel, self).save(*args, **kwargs)

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        self.fix_datetimes()

        if self.pk:
            try:
                dict_old = self.__get_dictionary_for_compare(self.__class__.objects.get(pk=self.pk))
                dict_new = self.__get_dictionary_for_compare(self)
                diff = DictDiffer(dict_old, dict_new)
                changed = diff.changed()
                if changed:
                    self.__check_update_permissions(changed)
            except ObjectDoesNotExist:
                pass
        else:
            self.__check_create_permissions()
        return super(BaseModel, self).save(*args, **kwargs)

    def delete(self):
        self.__check_delete_permissions()
        return super(BaseModel, self).delete()

    def autopopulate_by_ownership(self):
        pass

    def __check_update_permissions(self, fields):
        if not self.permission_check:
            return

        if 'user' not in REGISTRY or REGISTRY['user'] is None or REGISTRY['user'].is_anonymous():
            from restapi.models.User import User
            if self.__class__ == User:
                return

        user = REGISTRY['user']

        if not bool(user.check_instance_permission(instance=self, action='update')):
            raise PermissionDeniedException()

        can_update_fields = user.get_permitted_model_fields(model=self.__class__, action='update', fields=fields)
        rejected = set(fields) - set(can_update_fields)
        if rejected:
            raise PermissionDeniedException()

    def __check_create_permissions(self):
        if not self.permission_check:
            return
        user = REGISTRY['user']
        create_permission = user.check_instance_permission(instance=self, action='create')
        if not create_permission:
            raise PermissionDeniedException()
        if create_permission == 'own':
            self.autopopulate_by_ownership()

    def __check_delete_permissions(self):
        if not self.permission_check:
            return
        user = REGISTRY['user']
        if not bool(user.check_instance_permission(instance=self, action='delete')):
            raise PermissionDeniedException()

    # pylint: disable=no-self-use
    def __get_dictionary_for_compare(self, obj):
        data = obj.as_dict()
        data.pop('last_update', None)

        for field, value in data.items():
            if isinstance(value, datetime):
                data[field] = value.replace(tzinfo=None)
        return data

    class Meta:
        abstract = True


class BasePausedAtModelMixin(object):
    def save(self, update_fields=None, *args, **kwargs):
        old_status = self.__class__.objects.get(pk=self.pk).status if self.pk else None
        # status has been changed to 'paused'
        if bool(self.pk) and self.status == STATUS_PAUSED and old_status != STATUS_PAUSED:
            # pylint: disable=attribute-defined-outside-init
            self.paused_at = datetime.now(tzutc())
        # status has been changed from 'paused'
        elif old_status == STATUS_PAUSED and self.status != STATUS_PAUSED:
            # pylint: disable=attribute-defined-outside-init
            self.paused_at = None
        if update_fields is not None:
            update_fields = tuple(list(update_fields) + ['paused_at'])
        return super(BasePausedAtModelMixin, self).save(update_fields=update_fields, *args, **kwargs)


class BaseReadonlyModelMixin(object):
    # pylint: disable=unused-argument
    def save(self, *args, **kwargs):
        raise ReadOnlyModelWriteException(
            {'Access forbidden': 'Attempt to save into the readonly model: %s' % self.__class__})

    # pylint: disable=unused-argument
    def delete(self, *args, **kwargs):
        raise ReadOnlyModelWriteException(
            {'Access forbidden': 'Attempt to delete from the readonly model: %s' % self.__class__})


class DictDiffer(object):
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])
