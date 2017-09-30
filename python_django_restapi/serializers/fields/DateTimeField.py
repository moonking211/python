from datetime import datetime
from dateutil.parser import parse
import re

import six

from django.conf import settings
import pytz
from pytz import timezone
from rest_framework import serializers


TZ = timezone(settings.TIME_ZONE)


class DateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        if value and isinstance(value, datetime):
            if value.year < 1900:
                value = value.replace(year=1900)
            value = value.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return value

    def to_internal_value(self, data):
        if isinstance(data, datetime):
            return data
        if isinstance(data, six.string_types):
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3}|)Z$', data):
                raise serializers.ValidationError('Use a valid format: 0000-00-00T00:00:00Z')
            return parse(data)
        return data


class ZeroDateTimeField(DateTimeField):
    def to_internal_value(self, data):
        if isinstance(data, datetime):
            return data
        if data == '' or data == '0000-00-00 00:00:00':
            return None
        return super(ZeroDateTimeField, self).to_internal_value(data)


class WideRangeDateTimeField(DateTimeField):
    def to_representation(self, value):
        if value:
            if value.year <= 1000:
                value = '1000-01-01T00:00:00Z'
            elif value.year >= 9000:
                value = '9999-12-31T23:59:59Z'
        value = super(WideRangeDateTimeField, self).to_representation(value)
        return value

    def to_internal_value(self, data):
        return super(WideRangeDateTimeField, self).to_internal_value(data)
