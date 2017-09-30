import json

import six

from datetime import timedelta
from django.db import models

from restapi.models.choices import SIZE_ALL
from restapi.time_shifting import PacificTimeShift


# pylint: disable=invalid-name
cmp_asterisk_last = lambda a, b: 1 if a == '*' else -1 if b == '*' else 0


# pylint: disable=invalid-name
def cmp_lines_asterisk_last(a, b):
    if len(a) and a[0] == '*':
        return 1
    if len(b) and b[0] == '*':
        return -1
    return 0


class JSONField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a JSON"

    def __init__(self, *args, **kwargs):
        self.default_json = kwargs.pop('default_json', dict)
        super(JSONField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value:
            if isinstance(value, six.string_types):
                value = json.loads(value)
        else:
            value = self.default_json()
        return value

    def get_prep_value(self, value):
        return json.dumps(value)


class OrderedJSONField(JSONField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a JSON with ordered elements"

    def __init__(self, *args, **kwargs):
        # pylint: disable=unnecessary-lambda
        self.cmp = kwargs.pop('cmp', lambda a, b: cmp(a, b))
        super(OrderedJSONField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        json_elements = []

        if value == "":
            return value

        for k in sorted(value.keys(), cmp=self.cmp):
            # pylint: disable=invalid-name
            v = value[k]
            key = '"%s"' % k
            val = '"%s"' % v if isinstance(v, six.string_types) else v
            json_elements.append("%s:%s" % (key, val))

        json_string = "{" + ",".join(json_elements) + "}"
        return  json_string


class OrderedTextField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a text with ordered lines"

    def __init__(self, *args, **kwargs):
        # pylint: disable=unnecessary-lambda
        self.cmp = kwargs.pop('cmp', lambda a, b: cmp(a, b))
        super(OrderedTextField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        lines = value.split('\n')
        text = '\n'.join(sorted(lines, cmp=self.cmp))
        return text


class ZeroDateField(models.DateField):
    def get_db_prep_value(self, value, connection, prepared=False):
        # Casts datetimes into the format expected by the backend
        if not prepared:
            value = self.get_prep_value(value)
        # Use zeroed datetime instead of NULL
        if value is None:
            return "0000-00-00"
        else:
            return connection.ops.value_to_db_date(value)


class DateTimeField(models.DateTimeField):
    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_value(value)
        # Casts datetimes into the format expected by the backend
        new_value = self.get_db_backend_prep_value(value)
        if not new_value is value:
            value = new_value
        else:
            if value is not None:
                value += timedelta(hours=PacificTimeShift.get(value))
            value = connection.ops.value_to_db_datetime(value)
        return value

    # pylint: disable=no-self-use
    def get_db_backend_prep_value(self, value):
        return value


class ZeroDateTimeField(DateTimeField):
    def get_db_backend_prep_value(self, value):
        if value is None:
            value = "0000-00-00 00:00:00"
        return value


class WideRangeDateTimeField(DateTimeField):
    def get_db_backend_prep_value(self, value):
        if value and value.year <= 1000:
            value = "1000-01-01 00:00:00"
        elif value and value.year >= 9000:
            value = '9999-12-31 23:59:59'
        return value


class SizeCharField(models.CharField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(SizeCharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        value = super(SizeCharField, self).to_python(value)
        return SIZE_ALL if value is None or not value else value

    def get_prep_value(self, value):
        value = self.to_python(super(SizeCharField, self).get_prep_value(value))
        return None if value == SIZE_ALL or not value else value
