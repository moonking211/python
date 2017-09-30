from datetime import datetime
from rest_framework import serializers


class ZeroDateField(serializers.DateTimeField):

    def to_representation(self, value):
        if isinstance(value, datetime):
            try:
                return value.strftime("%Y-%m-%d")
            except ValueError:
                return None
        return value

    def to_internal_value(self, data):
        if data == '':
            return None
        return data
